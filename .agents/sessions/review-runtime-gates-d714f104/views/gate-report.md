# Gate Report

- review_id: review-20260506T191637Z
- status: completed
- schema_version: 1.0.0
- profile: standard

## lint
- status: failed
- blocking: true
- classification: code
- exit_code: 1
- command: python3 -c "import sys; print('lint failed'); sys.exit(1)"
- duration_seconds: 0.017
## tests
- status: failed
- blocking: false
- classification: code
- exit_code: 1
- command: python3 -c "import sys; print('tests advisory'); sys.exit(1)"
- duration_seconds: 0.016
