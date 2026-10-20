The price list is Ines's, byte for byte, and your note of the phone
call is still in the dispatch log.

`git restore --theirs` and `--ours` are for the conflicts where one
side is simply right. They replace one file with one side's version,
whole: no markers to miss, no figures to mistype. The rest of the merge
still happens as normal, which is why your log line survived.

Next job: the same move, the other way round.
