import os
import sys
from aspirin.pytester.fixturer import dbc


src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(src_dir)

# localhost
dbc(__name__, uri='mysql://localhost/postgkh', dbc_alias='dbc')
# tdev227
# dbc(__name__, uri='postgresql://postgres:[eq@localhost/vostok_test', dbc_alias='dbc')
