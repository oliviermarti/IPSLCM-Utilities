from colorama import Fore, Back, Style

UNDERLINE = '\033[4;37;48m'

WARNING = f'{Fore.RED}'
ERROR   = f'{Style.BRIGHT}{Fore.RED}'
FATAL   = f'{Style.BRIGHT}{Fore.RED}{Back.YELLOW}'
EMP     = f'{Fore.CYAN}'
STRONG  = f'{Style.BRIGHT}{Fore.CYAN}'
TITLE   = f'{Style.BRIGHT}{Fore.BLUE}{Back.WHITE}'
OK      = f'{Style.BRIGHT}{Fore.GREEN}'
KO      = f'{Style.BRIGHT}{Fore.RED}'
MESG    = f'{Style.BRIGHT}{Fore.CYAN}'
NORM    = f'{Style.RESET_ALL}'
