## Order of tests

It makes sense to test individual components (unit tests) first, since when those have a bug end2end tests (calling cipug) will also fail. Unit tests can give better insight though what is broken, since there are fewer moving parts than with end2end tests.

For this reason tests are grouped into `test_A_unit_tests` and `test_B_end2end_tests`. The uppercase character makes pytest execute them in correct order. More levels can be added on demand (integration tests?).
