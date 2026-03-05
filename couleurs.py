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

# https://bdevs.net/color-palettes/color-blind-friendly/
Classic_CB_Safe = ['#0072B2', '#E69F00', '#800080', '#009E73', '#D55E00']
Sky_and_Sun     = ['#56B4E9', '#FFA500', '#CC79A7', '#009900', '#0072B2']

# From Paul Tol: https://personal.sron.nl/~pault/
Tol_bright = ['#EE6677', '#228833', '#4477AA', '#CCBB44', '#66CCEE', '#AA3377', '#BBBBBB']
Tol_muted  = ['#88CCEE', '#44AA99', '#117733', '#332288', '#DDCC77', '#999933', '#CC6677', '#882255', '#AA4499', '#DDDDDD']
Tol_light  = ['#BBCC33', '#AAAA00', '#77AADD', '#EE8866', '#EEDD88', '#FFAABB', '#99DDFF', '#44BB99', '#DDDDDD']

# From Color Universal Design (CUD): https://jfly.uni-koeln.de/color/
Okabe_Ito = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7", "#000000"]

# 'noir', 'gris foncé', 'gris souris', 'blanc', 'gris violet fonce', 'vert canard', 'vert bleu', 'vert eclatant', 'violet', 'bleu azure', 'mauve', 'rose', 'rouge brun', 'orange brun', 'jaune'
couleurs_aaa = [ '#000000', '#252525', '#676767', '#FFFFFF', '#171723', '#004949', '#009999', '#22CF22', '#490092', '#006DDB', '#B66DFF', '#FF6DB6', '#920000', '#DB6D00', '#FFDF4D' ]


