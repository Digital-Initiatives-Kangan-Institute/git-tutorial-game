"""The watcher: engine thread, browser state and HTTP server, against real repos."""

from __future__ import annotations

import http.client
import json
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from git_tutorial.levels.pack import discover_pack
from git_tutorial.session.lifecycle import Session
from git_tutorial.testing.builder import RepoBuilder
from git_tutorial.testing.clock import FakeClock
from git_tutorial.web.engine import Engine
from git_tutorial.web.server import Server, asset, serve
from tests.conftest import write_level

pytestmark = pytest.mark.integration


@pytest.fixture
def engine(session: Session) -> Engine:
    session.begin_level("level-1")
    return Engine(session, clock=FakeClock())


@pytest.fixture
def asking(session: Session, pack_root: Path) -> Engine:
    """level-1 with a question on its job sheet as well as a branch to make."""
    write_level(
        pack_root / "levels" / "level-1", "level-1", number=1,
        setup_body="def setup(repo, state):\n    repo.delete_branch('rescue', force=True)\n",
        assertions=(
            "- {kind: branch_exists, name: rescue, label: 'Create the branch `rescue`',"
            " story: 'Open a new bay'}\n"
            "- {kind: answer, id: colour, equals: blue, prompt: 'Which colour?'}\n"
        ),
    )
    session.pack = discover_pack(pack_root)
    session.begin_level("level-1")
    return Engine(session, clock=FakeClock())


def worktree(engine: Engine) -> Path:
    return engine.session.worktree


class TestTheState:
    def test_the_first_step_publishes_everything_the_page_draws(self, engine: Engine) -> None:
        assert engine.step()
        state = engine.current
        assert state["seq"] == 1
        assert state["phase"] == "working"
        assert state["level"]["id"] == "level-1"
        assert state["level"]["intro"][-1] == {"type": "try", "commands": ["git status"]}
        assert [g["kind"] for g in state["goals"]] == ["branch_exists"]
        assert state["warehouse"]["shelves"][0]["name"] == "main"
        assert state["course"][0]["levels"][0]["status"] == "current"
        json.dumps(state)  # it has to survive the wire

    def test_nothing_changed_means_nothing_published(self, engine: Engine) -> None:
        engine.step()
        assert not engine.step()
        assert engine.current["seq"] == 1

    def test_an_edit_with_no_git_command_still_shows(self, engine: Engine) -> None:
        engine.step()
        (worktree(engine) / "seed.txt").write_text("edited\n", encoding="utf-8")
        assert engine.step()
        floor = engine.current["warehouse"]["floor"]
        assert {"path": "seed.txt", "mark": "~"} in floor
        assert engine.current["move"]["command"] == "edited"

    def test_goals_carry_label_and_story(self, asking: Engine) -> None:
        asking.step()
        goal = asking.current["goals"][0]
        assert goal["label"] == "Create the branch `rescue`"
        assert goal["story"] == "Open a new bay"
        assert asking.current["goals"][1]["answer"]["prompt"] == "Which colour?"


class TestCommands:
    def run(self, engine: Engine, kind: str, data: dict[str, Any]) -> dict[str, Any]:
        """submit() from another thread, the way an HTTP handler calls it."""
        box: dict[str, Any] = {}
        thread = threading.Thread(target=lambda: box.update(engine.submit(kind, data)))
        thread.start()
        while thread.is_alive():
            engine.step()
            thread.join(0.01)
        return box

    def test_an_answer_is_recorded_and_graded(self, asking: Engine) -> None:
        asking.step()
        assert self.run(asking, "answer", {"id": "colour", "value": "blue"})["ok"]
        assert asking.current["goals"][1]["passed"]
        assert asking.current["goals"][1]["answer"]["value"] == "blue"

    def test_an_unknown_question_is_refused(self, asking: Engine) -> None:
        asking.step()
        result = self.run(asking, "answer", {"id": "nope", "value": "x"})
        assert not result["ok"] and result["status"] == 400

    def test_a_command_for_an_old_level_is_refused(self, asking: Engine) -> None:
        asking.step()
        result = self.run(asking, "answer", {"level": "level-2", "id": "colour", "value": "x"})
        assert result["status"] == 409

    def test_hints_climb_one_rung_at_a_time(self, engine: Engine) -> None:
        engine.step()
        assert self.run(engine, "hint", {})["ok"]
        assert [h["rung"] for h in engine.current["hints"]["shown"]] == [1]
        assert self.run(engine, "hint", {})["ok"]
        assert not self.run(engine, "hint", {})["ok"]
        assert engine.current["hints"]["more"] is False

    def test_next_waits_for_completion_then_runs_setup(self, engine: Engine) -> None:
        engine.step()
        assert self.run(engine, "next", {})["status"] == 409

        engine.session.repo.git("branch", "rescue")
        engine.step()
        assert engine.current["phase"] == "complete"
        assert any(e["kind"] == "level_complete" for e in engine.current["events"])
        assert engine.current["success"]["learned"] == []

        assert self.run(engine, "next", {})["ok"]
        assert engine.current["level"]["id"] == "level-2"
        assert engine.current["phase"] == "working"
        assert any(e["kind"] == "level_arrived" for e in engine.current["events"])

    def test_completion_never_advances_by_itself(self, engine: Engine) -> None:
        engine.step()
        engine.session.repo.git("branch", "rescue")
        for _ in range(3):
            engine.step()
        assert engine.current["level"]["id"] == "level-1"

    def test_reset_puts_the_level_back(self, engine: Engine) -> None:
        engine.step()
        (worktree(engine) / "target.txt").unlink()
        assert self.run(engine, "reset", {})["ok"]
        assert (worktree(engine) / "target.txt").exists()

    def test_an_idle_student_is_offered_a_hint(self, session: Session) -> None:
        clock = FakeClock()
        session.clock = clock
        session.begin_level("level-1")
        engine = Engine(session, clock=clock)
        engine.step()
        clock.advance(400)
        engine.step()
        assert engine.current["hints"]["shown"], "the ladder should have reached rung 1"
        assert any(e["kind"] == "hint" and not e["asked"] for e in engine.current["events"])


class TestWaiting:
    def test_wait_returns_at_once_when_behind(self, engine: Engine) -> None:
        engine.step()
        assert engine.wait(-1, timeout=5)["seq"] == 1

    def test_wait_times_out_when_nothing_changes(self, engine: Engine) -> None:
        engine.step()
        assert engine.wait(1, timeout=0.05)["seq"] == 1


# ---- over HTTP ---------------------------------------------------------------


@pytest.fixture
def server(asking: Engine) -> Iterator[Server]:
    stop = threading.Event()
    asking.step()
    httpd = serve(asking, port=0)
    threads = [
        threading.Thread(target=httpd.serve_forever, daemon=True),
        threading.Thread(target=asking.run, args=(stop,), daemon=True),
    ]
    for thread in threads:
        thread.start()
    yield httpd
    stop.set()
    httpd.shutdown()
    httpd.server_close()


def request(server: Server, method: str, path: str, *, body: Any = None,
            headers: dict[str, str] | None = None, host: str = "127.0.0.1") -> tuple[int, bytes]:
    conn = http.client.HTTPConnection("127.0.0.1", server.port, timeout=10)
    sent = {"Host": f"{host}:{server.port}", **(headers or {})}
    payload = None if body is None else json.dumps(body).encode()
    conn.request(method, path, body=payload, headers=sent)
    response = conn.getresponse()
    return response.status, response.read()


def trusted(server: Server) -> dict[str, str]:
    return {"Origin": f"http://127.0.0.1:{server.port}", "Content-Type": "application/json",
            "X-WT-Token": server.token}


class TestServer:
    def test_the_page_and_its_assets_ship_inside_the_package(self) -> None:
        for name in ("index.html", "app.js", "app.css"):
            assert asset(name)

    def test_the_page_carries_this_runs_token(self, server: Server) -> None:
        status, body = request(server, "GET", "/")
        assert status == 200
        assert server.token.encode() in body
        assert b"__WT_TOKEN__" not in body

    def test_state_is_served_as_json(self, server: Server) -> None:
        status, body = request(server, "GET", "/state?since=-1")
        assert status == 200
        assert json.loads(body)["level"]["id"] == "level-1"

    def test_a_foreign_host_is_refused(self, server: Server) -> None:
        assert request(server, "GET", "/state?since=-1", host="attacker.example")[0] == 403

    @pytest.mark.parametrize("drop", ["Origin", "Content-Type", "X-WT-Token"])
    def test_a_post_without_every_credential_is_refused(self, server: Server, drop: str) -> None:
        headers = {k: v for k, v in trusted(server).items() if k != drop}
        status, _ = request(server, "POST", "/hint", body={}, headers=headers)
        assert status == 403

    def test_a_post_from_another_origin_is_refused(self, server: Server) -> None:
        headers = {**trusted(server), "Origin": "http://attacker.example"}
        assert request(server, "POST", "/hint", body={}, headers=headers)[0] == 403

    def test_an_answer_posted_from_the_page_is_graded(self, server: Server) -> None:
        status, body = request(server, "POST", "/answer", body={"id": "colour", "value": "blue"},
                               headers=trusted(server))
        assert status == 200 and json.loads(body)["ok"]
        _, raw = request(server, "GET", "/state?since=-1")
        assert json.loads(raw)["goals"][1]["passed"]

    def test_next_before_completion_is_a_conflict(self, server: Server) -> None:
        status, body = request(server, "POST", "/next", body={}, headers=trusted(server))
        assert status == 409
        assert "finish" in json.loads(body)["error"]

    def test_unknown_paths_are_404(self, server: Server) -> None:
        assert request(server, "GET", "/etc/passwd")[0] == 404
        assert request(server, "POST", "/delete-everything", body={},
                       headers=trusted(server))[0] == 404


class TestOtherProcesses:
    def test_a_job_finished_from_the_terminal_is_still_announced(self, engine: Engine) -> None:
        """`wt solve` and `wt check` complete jobs from their own process."""
        engine.step()
        engine.session.repo.git("branch", "rescue")
        engine.session.check()  # what `wt check` does, out of the engine's sight
        engine.step()
        events = [e for e in engine.current["events"] if e["kind"] == "level_complete"]
        assert len(events) == 1
        engine.step()
        assert len([e for e in engine.current["events"] if e["kind"] == "level_complete"]) == 1


class TestTheYard:
    """The yard is for what this job loses, not what the course tidied away."""

    def test_earlier_jobs_work_wound_back_by_setup_is_not_drawn(
        self, session: Session, pack_root: Path
    ) -> None:
        start = session.repo.git("rev-parse", "HEAD").stdout.strip()
        write_level(
            pack_root / "levels" / "level-2", "level-2", number=2,
            setup_body=f"def setup(repo, state):\n    repo.reset_hard('{start}')\n",
            assertions="- {kind: branch_exists, name: second}\n",
        )
        session.pack = discover_pack(pack_root)
        session.repo.write("mine.txt", "student work\n").commit("the student's own commit")
        session.begin_level("level-2")
        engine = Engine(session, clock=FakeClock())
        engine.step()
        assert engine.current["warehouse"]["yard"] == []

    def test_an_incident_the_setup_stages_is_drawn(
        self, session: Session, pack_root: Path
    ) -> None:
        write_level(
            pack_root / "levels" / "level-2", "level-2", number=2,
            setup_body=(
                "def setup(repo, state):\n"
                "    repo.write_file('lost.txt', 'lost\\n')\n"
                "    repo.commit('a commit the incident loses')\n"
                "    repo.reset_hard('HEAD~1')\n"
            ),
            assertions="- {kind: branch_exists, name: second}\n",
        )
        session.pack = discover_pack(pack_root)
        session.begin_level("level-2")
        engine = Engine(session, clock=FakeClock())
        engine.step()
        subjects = [c["subject"] for c in engine.current["warehouse"]["yard"]]
        assert subjects == ["a commit the incident loses"]

    def test_a_colleagues_commit_waiting_at_head_office_is_not_drawn(
        self, session: Session, pack_root: Path, tmp_path: Path
    ) -> None:
        """Act 4's setups commit as Ines, push, and wind back: the commit is
        not lost, it is at Head Office waiting to be fetched."""
        bare = tmp_path / "head-office.git"
        session.repo.git("init", "--bare", "-b", "main", str(bare))
        session.repo.git("remote", "add", "origin", str(bare))
        session.repo.git("push", "-u", "origin", "main")
        write_level(
            pack_root / "levels" / "level-2", "level-2", number=2,
            setup_body=(
                "def setup(repo, state):\n"
                "    repo.write_file('ines.txt', 'from Head Office\\n')\n"
                "    repo.commit('Ines sends this up')\n"
                "    repo.git('push', 'origin', 'HEAD:main')\n"
                "    repo.reset_hard('HEAD~1')\n"
                "    repo.git('update-ref', 'refs/remotes/origin/main', 'HEAD')\n"
            ),
            assertions="- {kind: branch_exists, name: second}\n",
        )
        session.pack = discover_pack(pack_root)
        session.begin_level("level-2")
        engine = Engine(session, clock=FakeClock())
        engine.step()
        assert engine.current["warehouse"]["yard"] == []
        assert engine.current["warehouse"]["unseen"] == 1


class TestTeamPicture:
    def test_tags_and_head_office_are_drawn(
        self, session: Session, tmp_path: Path
    ) -> None:
        bare = tmp_path / "head-office.git"
        repo = session.repo
        repo.git("init", "--bare", "-b", "main", str(bare))
        repo.git("remote", "add", "origin", str(bare))
        repo.git("push", "-u", "origin", "main")
        repo.git("push", "origin", "main:old-bay")
        repo.git("fetch")
        # Deleted at Head Office by someone else; a plain fetch keeps the note.
        repo.git("--git-dir", str(bare), "branch", "-D", "old-bay")
        repo.git("fetch")
        repo.git("tag", "stocktake-march")
        session.begin_level("level-1")
        engine = Engine(session, clock=FakeClock())
        engine.step()
        w = engine.current["warehouse"]
        assert [t["name"] for t in w["tags"]] == ["stocktake-march"]
        assert w["office"]["branches"] == ["main"]
        stale = {r["name"]: r["stale"] for r in w["remotes"]}
        assert stale["origin/old-bay"] is True and stale["origin/main"] is False

    def _office(self, session: Session, tmp_path: Path) -> Path:
        bare = tmp_path / "head-office.git"
        session.repo.git("init", "--bare", "-b", "main", str(bare))
        session.repo.git("remote", "add", "origin", str(bare))
        session.repo.git("push", "-u", "origin", "main")
        return bare

    def test_a_colleagues_pruned_branch_does_not_fill_the_yard(
        self, session: Session, tmp_path: Path
    ) -> None:
        """Pruning removes a name and its reflog. A colleague's commits on a
        branch Head Office deleted were never the student's to lose."""
        bare = self._office(session, tmp_path)
        colleague = tmp_path / "colleague"
        session.repo.git("clone", "-q", str(bare), str(colleague))
        other = RepoBuilder(colleague, home=tmp_path / "githome")
        other.git("switch", "-c", "old-bay")
        other.write("old.txt", "old\n").commit("a colleague's bay, later deleted")
        other.git("push", "origin", "old-bay")
        session.repo.git("fetch")
        other.git("push", "origin", "--delete", "old-bay")
        session.begin_level("level-1")
        engine = Engine(session, clock=FakeClock())
        engine.step()

        session.repo.git("fetch", "--prune")
        engine.step()
        w = engine.current["warehouse"]
        assert "origin/old-bay" not in [r["name"] for r in w["remotes"]]
        assert engine.current["move"]["command"] == "git fetch --prune"
        assert w["yard"] == []

    def test_the_students_own_deleted_work_does_show(
        self, session: Session, tmp_path: Path
    ) -> None:
        """HEAD's reflog still names it, so the yard's caption is true."""
        session.repo.git("switch", "-c", "scrap")
        session.repo.write("scrap.txt", "x\n").commit("work the student threw away")
        session.repo.git("switch", "main")
        session.begin_level("level-1")
        engine = Engine(session, clock=FakeClock())
        engine.step()
        session.repo.git("branch", "-D", "scrap")
        engine.step()
        subjects = [c["subject"] for c in engine.current["warehouse"]["yard"]]
        assert subjects == ["work the student threw away"]

    def test_a_branch_setup_published_then_pruned_does_not_fill_the_yard(
        self, session: Session, pack_root: Path, tmp_path: Path
    ) -> None:
        """Act 5.04's shape: setup makes a colleague's branch here, sends it
        to Head Office, winds it back, and Head Office deletes it."""
        bare = self._office(session, tmp_path)
        write_level(
            pack_root / "levels" / "level-2", "level-2", number=2,
            setup_body=(
                "def setup(repo, state):\n"
                "    repo.git('switch', '-c', 'old-bay')\n"
                "    repo.write_file('old.txt', 'old\\n')\n"
                "    repo.commit('a colleague bay')\n"
                "    repo.git('push', 'origin', 'old-bay')\n"
                "    repo.git('switch', 'main')\n"
                "    repo.git('branch', '-D', 'old-bay')\n"
                f"    repo.git('--git-dir', {str(bare)!r}, 'branch', '-D', 'old-bay')\n"
            ),
            assertions="- {kind: branch_exists, name: second}\n",
        )
        session.pack = discover_pack(pack_root)
        session.begin_level("level-2")
        engine = Engine(session, clock=FakeClock())
        engine.step()
        session.repo.git("fetch", "--prune")
        engine.step()
        assert engine.current["move"]["command"] == "git fetch --prune"
        assert engine.current["warehouse"]["yard"] == []


class TestConflictPicture:
    def test_a_stopped_pull_is_named_and_blocks_are_counted(
        self, session: Session, tmp_path: Path
    ) -> None:
        bare = tmp_path / "head-office.git"
        repo = session.repo
        repo.git("init", "--bare", "-b", "main", str(bare))
        repo.git("remote", "add", "origin", str(bare))
        repo.git("push", "-u", "origin", "main")
        other = RepoBuilder(tmp_path / "colleague", home=tmp_path / "githome")
        repo.git("clone", "-q", str(bare), str(other.path))
        other.write("seed.txt", "theirs 1\na\nb\nc\nd\ntheirs 2\n").commit("theirs")
        other.git("push", "-q")
        repo.write("seed.txt", "ours 1\na\nb\nc\nd\nours 2\n").commit("ours")
        session.begin_level("level-1")
        repo.git("pull", "--no-rebase", "--no-edit", check=False)
        engine = Engine(session, clock=FakeClock())
        engine.step()
        w = engine.current["warehouse"]
        assert w["hold_from"] == "pull"
        held = next(i for i in w["floor"] if i["path"] == "seed.txt")
        assert held["detail"] == "both changed" and held["blocks"] == 2
