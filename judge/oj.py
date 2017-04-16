
# Common define

Judge_WT = 0  # in vjudge waiting queue
Judge_AC = 1
Judge_PE = 2
Judge_TLE = 3
Judge_MLE = 4
Judge_WA = 5
Judge_RE = 6
Judge_OLE = 7
Judge_CE = 8
Judge_JE = 9 # judged, but failed!
Judge_JG = 10 # first judge, judging, is waiting or runing on the target oj

# must check other oj submit judge script, time:2016-10-14 22:37
Judge_RF = 11 # Restricted function # add time: 2016-10-14 22:34
Judge_AC_PART = 12 # Accepted partial case

# seprate by 64
Judge_SUBMIT_ERROR = 65 # Submit error # add time: 2016-10-14 22:34
Judge_SYSTEM_ERROR = 66 # System error # add time: 2016-10-14 22:34
Judge_FIREWAL_FORBID = 67 # add time: 2016-10-14 22:34

class CommonException(Exception):
    """CommonException, Common Exception"""
    pass

class JudgeException(Exception):
    """Code Length Invalid"""
    pass
 
class CodeLengthTooShortException(JudgeException):
    """Code Length Too Short"""
    pass

class CodeLengthTooLongException(JudgeException):
    """Code Length Too Long"""
    pass

class CodeLengthInvalidException(JudgeException):
    """Code Length Invalid"""
    pass
        
class LoginFailedException(JudgeException):
    """Login Failed Exception"""
    pass

class SubmitFailedException(JudgeException):
    """Submit Failed Exception"""
    pass

class ResultFailedException(JudgeException):
    """ResultFailed Exception"""
    pass

class NotFoundOJException(JudgeException) :
    """Not Found OJ Module"""
    pass

class InvalidLanguageException(JudgeException) :
    """Invalid Language"""
    pass

class ParseResultException(JudgeException) :
    """Parse Result Exception"""
    pass

class FirewallDenyOJException(JudgeException) :
    """Firewall Deny !"""
    pass

