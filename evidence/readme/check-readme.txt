$ python3 scripts/proofs/check_readme.py sections
ok   sections in order: ['Quick start', 'Demo with curl', 'Postman collection', 'Sample PDFs', 'Architecture', 'API reference', 'Decisions', 'Departures from the brief', 'Gaps found in the brief', 'Limits and budget', 'How I worked', 'Testing and evidence', 'What I would do next', 'Time spent']
ok   architecture holds the flowchart
ok   architecture holds the state diagram
ok   API reference shows the envelope
ok   quick start is one docker compose up
result: PASSED

$ python3 scripts/proofs/check_readme.py how-i-worked
ok   mentions 'harness'
ok   mentions 'brief'
ok   mentions 'tlc-spec-lean'
ok   mentions 'frontend-blueprint'
ok   mentions 'slice by slice'
ok   mentions 'fresh-subagent review'
ok   mentions '/review-before-push'
ok   in order: [6, 383, 532, 826, 1076, 1249, 1435]
result: PASSED

$ python3 scripts/proofs/check_readme.py budget
ok   states the key holds $5
ok   states the daily budget of 3,000 model pages
ok   names provider_out_of_credits
ok   says what a reviewer sees when credit runs out
result: PASSED

$ python3 scripts/proofs/check_readme.py postman-and-samples
ok   collection has POST /api/v1/sessions
ok   collection has POST /api/v1/documents
ok   collection has GET /api/v1/documents
ok   collection has GET /api/v1/documents/{{documentId}}
ok   collection has GET /api/v1/documents/{{documentId}}/pages
ok   collection has POST /api/v1/documents/{{documentId}}/reparse
ok   collection has POST /api/v1/documents/{{documentId}}/requeue
ok   collection has DELETE /api/v1/documents/{{documentId}}
ok   collection has GET /api/v1/budget
ok   collection has GET /api/v1/health/live
ok   collection has GET /api/v1/health/ready
ok   collection has exactly 11 routes
ok   text sample w3c-dummy.pdf exists
ok   w3c-dummy.pdf has a line in samples/SOURCES.md
ok   over 10 pages sample constitution-of-the-united-states.pdf exists
ok   constitution-of-the-united-states.pdf has a line in samples/SOURCES.md
ok   scanned sample constitution-scanned-p1-3.pdf exists
ok   constitution-scanned-p1-3.pdf has a line in samples/SOURCES.md
ok   encrypted sample w3c-dummy-locked.pdf exists
ok   w3c-dummy-locked.pdf has a line in samples/SOURCES.md
ok   SOURCES.md names licenses
ok   README prints the demo password
result: PASSED

