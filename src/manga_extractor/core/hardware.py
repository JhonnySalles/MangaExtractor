import os
import tensorflow as tf
from manga_extractor.core.classes import PrintLog

class HardwareManager:
    def __init__(self, mode='auto', window=None):
        """
        mode: 'cpu', 'gpu', 'auto'
        """
        self.mode = mode.lower()
        self.window = window
        self.gpus = []
        self.use_gpu = False
        self._detect_hardware()
        self._configure()

    def _log(self, message, color=None):
        if self.window:
            self.window.write_event_value('-THREAD_LOG-', PrintLog(message, color))
        else:
            print(message)

    def _detect_hardware(self):
        """Detecta GPUs via tf.config.list_physical_devices('GPU')"""
        if self.mode == 'cpu':
            self._log("Hardware Manager: Forçando modo CPU.", 'yellow')
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
            return

        try:
            physical_gpus = tf.config.list_physical_devices('GPU')
            if physical_gpus:
                self.gpus = physical_gpus
                self.use_gpu = True
                self._log(f"Hardware Manager: {len(self.gpus)} GPU(s) detectada(s).", 'green')
                for i, gpu in enumerate(self.gpus):
                    self._log(f"  - GPU {i}: {gpu.name}", 'green')
            else:
                self._log("Hardware Manager: Nenhuma GPU detectada. Usando CPU.", 'yellow')
                self.use_gpu = False
        except Exception as e:
            self._log(f"Hardware Manager: Erro ao detectar GPU: {e}. Usando CPU.", 'red')
            self.use_gpu = False

    def _configure(self):
        """Configura TensorFlow: set_memory_growth(True)"""
        if self.use_gpu:
            try:
                for gpu in self.gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                self._log("Hardware Manager: Memory growth habilitado para as GPUs.", 'green')
            except Exception as e:
                self._log(f"Hardware Manager: Erro ao configurar GPU: {e}", 'red')
        else:
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

    def get_use_gpu(self):
        return self.use_gpu
