import logging

import quizcomp.log
import tests.base

class TestLog(tests.base.BaseTest):
    def test_base_levels(self):
        quizcomp.log.init()

        print()
        logging.debug("log test: debug")
        logging.info("log test: info")
        logging.warning("log test: warning")
        logging.error("log test: error")
