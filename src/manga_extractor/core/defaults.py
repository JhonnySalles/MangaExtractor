



####################
##  APPLICATION
###################
APPLICATION_VERSION = 2

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
BD_NAME = 'manga_extractor'
BD_PARAMETER = dict(
    host='localhost',
    port=3306,
    user='admin',
    passwd='admin',
    database=BD_NAME
)

####################
##  TESSERACT
###################
DEFAULT_TESSERACT_FOLDER= "C:/Program Files/Tesseract-OCR"


####################
##  SILENT
###################
def PROCESS_ITEMS():
    from manga_extractor.core.classes import Operation
    operation = []
    operation.append(Operation("base",  "nome", r'F:/teste/jar', "ja", furigana=True, isSilent=True))

    return operation


####################
##  PARALLEL PROCESSING
###################
# Ativa o processamento paralelo (False = fluxo sequencial original)
PARALLEL_PROCESSING = True

# Número máximo de imagens processadas simultaneamente
# Controla a carga na CPU/GPU para evitar superaquecimento
MAX_PARALLEL_PAGES = 4

# Modo de processamento de hardware: 'cpu', 'gpu', 'auto'
PROCESSING_MODE = 'auto'

# Número máximo de workers para OCR (Tesseract/WinOCR)
MAX_OCR_WORKERS = 4

# Tamanho do batch para segmentação na GPU
GPU_BATCH_SIZE = 2