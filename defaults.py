from classes import Operacao


####################
##  APLICATIVO
###################
VERSAO_APLICATIVO = 1

####################
##  OCR
###################
BINARY_THRESHOLD = 190
GAUSSIAN_FILTER_SIGMA = 1.5
SEGMENTATION_THRESHOLD = 1
CC_SCALE_MAX = 4.0
CC_SCALE_MIN = 0.15
VERTICAL_SMOOTHING_MULTIPLIER = 0.75
HORIZONTAL_SMOOTHING_MULTIPLIER = 0.75
FURIGANA_WIDTH_THRESHOLD = 0.65
FURIGANA_DISTANCE_MULTIPLIER = 3.0  # 2.0
FURIGANA_VERTICAL_SIGMA_MULTIPLIER = 2.5  # 1.5
FURIGANA_HORIZONTAL_SIGMA_MULTIPLIER = 0.0
FURIGANA_BINARY_THRESHOLD = 240
MINIMUM_TEXT_SIZE_THRESHOLD = 7
MAXIMUM_VERTICAL_SPACE_VARIANCE = 5.0

FOLDER_SAVE_IMAGE_NOT_LOCATED_TEXT=r'F:/Manga/naoreconhecido/'

####################
##  BD
###################
NOME_DB = 'manga_extractor'
PARAMETROS_BD = dict(
    host='localhost',
    port=3306,
    user='admin',
    passwd='admin',
    database=NOME_DB
)

####################
##  TESSERACT
###################
DEFAULT_TESSERACT_FOLDER= "C:/Program Files/Tesseract-OCR"


####################
##  SILENT
###################
def ITENS_PROCESSAR():
    operacoes = []
    operacoes.append(Operacao("base",  "nome", r'F:/teste/jar', "ja", furigana=True, isSilent=True))

    return operacoes