from servlet.wsgi.falcon.graph_generation import Grapher
from servlet.wsgi.falcon.income_tracker import IncomeTracker

__author__ = 'sxh112430'

income_tracker = IncomeTracker()
grapher = Grapher()
grapher.score_vs_resources(1356)