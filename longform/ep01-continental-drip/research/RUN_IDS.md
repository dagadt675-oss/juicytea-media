# chapter workflows (resume with Workflow({scriptPath: research/chapter_workflow.js, resumeFromRunId, args}))
wf_e9f72d81-95e: ["ch1","ch4"]
wf_62c3a5cf-ed8: ["ch2","ch3"]
wf_a52c5edc-711: ["ch5a","ch6"]
wf_0b1483cf-3ba: ["ch5b"]
script workflow: wf_828e9517-122 (done)

# review round 6 (owner reported animation problems in the preview)
# animation review, per segment, find -> adversarial verify (script: ep01-animation-review)
wf_54d8968d-d4f: segments 1-4 (ch1, ch2)
wf_f838edbb-2a7: segments 5-7 (ch3, ch4, ch5a)
wf_9820647a-970: segments 8-10 (ch5b, ch6)
# retention / fatigue panel: casual, fan, strategist, fatigue lenses + voice/audio check -> synthesis
wf_96e8f33f-afb

# resumed after the usage limit (verify skipped; fix agents verify on the frames)
wf_54d8968d-d4f, wf_f838edbb-2a7, wf_9820647a-970 (resumed: S4, S7, S8, S10 finders), wf_96e8f33f-afb (resumed: voice/audio + synthesis)
# fix agents per module (verify -> fix -> test render)
wf_f960301e-cc0: ch1, ch3, ch4
