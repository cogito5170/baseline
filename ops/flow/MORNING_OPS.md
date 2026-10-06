# Ops morning list — user-only decisions (OPS-OVERNIGHT, until 10-07 09:00 KST). Overwrite, keep current.
Each: action the user takes / where / cause. Independent work continues without them.

1. R0-baseline tag: DONE by the user's AGY 01:55 KST (status AGY-ADMIN; tag at 318b22a). Ops cannot read ga-sdk from this session to confirm.
2. Archive GA57 01H2PH8B / old Dev hub 01Vtf8Jh: DONE (both archived, list_sessions 02:19 KST).
3. "하루 30 USD" window: KST calendar day or rolling 24 h? Ops proposes rolling for the cap, KST day for reports / top baseline / OP-OPS-VMHUB-R3.
4. VM policy integrity + kill switch (when VMHUB/R1 needs it): approve a root-owned VM-local policy file written only by you over SSH; set a spend limit on the VM's model API key at the provider console; know the Oracle console stop / GitHub credential revoke / OP-OPS-VMHUB-R3.
5. VM model credential (when R1 gateway needs a model): provide it on the VM yourself; never copied from a session / OPS-VMHUB rev3 constraint.
6. vm_policy.sessions {max_concurrent, max_children, timeout_s, per_day_usd} and push_allowed values / research/VMHUB_DESIGN.md §6.
7. VM_INTERIOR_DESIGN §13 user values (Ops defaults proposed in OP-OPS-VMINT): Q1 cutover time + integration ref; Q2 deadlines (Ops: plan 15 min, dispatch ack 10 min, verdict 30 min, integrate 30 min, deploy 2 h, observe 1 h); Q3 ladder values; Q4 confirm Ops owns slo.json with the proposed targets; Q6 create cogito5170/Dev and /Ops + VM push credential limited to shadow refs. (Q5=item 6, Q8=item 3, Q9=items 4-5; Q7 is a Dev+Ops contract, not yours.)
8. INTEGRATE refused by the platform classifier (Dev hub -> integrator 01Wz1byr; 01:41 tag, 02:02 INTEGRATE): accepted, not integrated: DEV-VI-06a-20 87e3243, DEV-R1-GW 3e7ab1c, DEV-VMSHA bb443ff (+ DEV-R2-DRY 451e980 once its solo rerun passes). Action: your own INTEGRATE line in integrator 01Wz1byr, or a send_message permission rule in the Dev session / cause: auto mode classifier.
9. worker-R0a director confirmation: RESOLVED by 03:0x (DEV-VMSHA verdict ACCEPT bb443ff, 749d727).
