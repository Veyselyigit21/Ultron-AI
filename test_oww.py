from openwakeword.model import Model
import numpy as np

try:
    owwModel = Model(wakeword_models=["hey_jarvis_v0.1"])
    # Feed silence
    audio = np.zeros(1280, dtype=np.int16)
    pred = owwModel.predict(audio)
    print("OpenWakeWord initialized! Predictions:", pred)
except Exception as e:
    print("Error:", e)
