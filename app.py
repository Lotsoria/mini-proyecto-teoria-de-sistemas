from flask import Flask, render_template, request, redirect, url_for
import sounddevice as sd
import soundfile as sf

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import resample
import io
import base64


app = Flask(__name__)

# Función para aplicar amplitud
def aplicar_amplitud(x, FS, aumento):
    try:
        y = aumento * x + x
        reproducir(y, FS)
    except Exception as e:
        print(f"Error al reproducir el audio: {e}")

# Función para reproducir audio
def reproducir(x, FS):
    try:
        sd.play(x, FS)
        # sd.wait()  # No es necesario esperar a que termine la reproducción
    except Exception as e:
        print(f"Error al reproducir el audio: {e}")

# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para manejar las opciones principales
@app.route('/opcion', methods=['POST'])
def opcion():
    opcion = int(request.form['opcion'])
    
    if opcion == 7:
        sd.stop()
    elif opcion == 3:
        return redirect(url_for('mostrar_amplitud'))
    elif opcion == 1:
        return redirect(url_for('mostrar_frecuencia_muestre'))
    elif opcion == 2:
        x, FS = sf.read('./static/Happy - Mono2.wav', dtype='float32')
        y = x[::-1]
        sd.play(y, FS)
        sd.wait()
    elif opcion == 4:
        return redirect(url_for('mostrar_extraer_audio'))
    elif opcion == 5:
        return redirect(url_for('procesar_audio'))

    return redirect(url_for('index'))

# Ruta para mostrar el menú de la opción 1
@app.route('/frecuencia_muestreo', methods=['GET'])
def mostrar_frecuencia_muestre():
    return render_template('frecuencia_muestreo.html')

# Ruta para la lógica de la opción 1
@app.route('/frecuencia_muestreo', methods=['POST'])
def frecuencia_muestreo():
    opcionFrecuencia = int(request.form['frecuencia'])
    x, FS = sf.read('./static/Happy - Mono2.wav', dtype='float32')

    if opcionFrecuencia == 5:
        sd.stop()
    elif opcionFrecuencia == 6:
        return redirect(url_for('index'))
    else:
        if opcionFrecuencia == 44100:
            reproducir(x, FS)
        elif opcionFrecuencia == 22050:
            FS = FS // 2
            reproducir(x, FS)
        elif opcionFrecuencia == 70000:
            FS = FS + 25900
            reproducir(x, FS)

    return redirect(url_for('mostrar_frecuencia_muestre'))

# Ruta para mostrar el menú de la opción 3
@app.route('/amplitud', methods=['GET'])
def mostrar_amplitud():
    return render_template('amplitud.html')

# Ruta para la lógica de la opción 3
@app.route('/amplitud', methods=['POST'])
def amplitud():
    opcionAumento = int(request.form['opcionAumento'])
    if opcionAumento == 5:
        sd.stop()
    elif opcionAumento == 6:
        return redirect(url_for('index'))
    else:
        aumento = float(request.form['aumento'])
        x, FS = sf.read('./static/Happy - Mono2.wav', dtype='float32')
        if opcionAumento == 1:
            aplicar_amplitud(x, FS, aumento)
        elif opcionAumento == 2:
            aplicar_amplitud(x, FS, -aumento)

    return redirect(url_for('mostrar_amplitud'))

# Ruta para mostrar el menú de la opción 4
@app.route('/extraer_audio', methods=['GET'])
def mostrar_extraer_audio():
    return render_template('extraer_audio.html')

# Ruta para la lógica de la opción 4
@app.route('/extraer_audio', methods=['POST'])
def extraer_audio():
    opcionAumento = int(request.form['opcion'])

    if opcionAumento == 5:
        sd.stop()
    elif opcionAumento == 6:
        return redirect(url_for('index'))
    else:
        inicio = int(request.form['inicio'])
        print(inicio)
        segundos = int(request.form['segundos'])
        print(segundos)
        x, FS = sf.read('./static/Happy - Mono2.wav', dtype='float32')
        
        # Validar que los valores no excedan la duración del audio
        duracion_total = len(x) / FS
        # render_template('extraer_audio.html', duracion=duracion_total, inicio=inicio, fin=inicio + segundos)
        print("debug duracion_total", duracion_total)
        if inicio + segundos > duracion_total:
            return render_template('extraer_audio.html',error = True , duracion_total=duracion_total, duracion_ingresada = inicio + segundos)

            # return "Error: El fragmento excede la duración del audio.", 400
        
        inicioMuestras = inicio * FS
        finMuestras = (inicio + segundos) * FS
        y = x[inicioMuestras:finMuestras]
        
        # Calcular la duración del fragmento extraído
        duracion_fragmento = len(y) / FS
        print("debug duracion_fragmento", duracion_fragmento)
        
        # Reproducir el fragmento
        sd.play(y, FS)

        return render_template('extraer_audio.html',duracion_total= duracion_total, duracion=duracion_fragmento, inicio=inicio, fin=inicio + segundos)


@app.route('/procesar_audio', methods=['GET', 'POST'])
def procesar_audio():
    if request.method == 'POST':
        x, FS = sf.read('./static/Happy - Mono2.wav', dtype='float32')
        inicio = 10
        duracion = 5

        inicio_muestras = int(inicio * FS)
        fin_muestras = int((inicio + duracion) * FS)
        fragmento_original = x[inicio_muestras:fin_muestras]

        # Aplicar escalamiento de amplitud de 1.5
        fragmento_amplificado = 1.5 * fragmento_original

        # Crear un retraso de 5 segundos agregando ceros al inicio
        retraso = np.zeros(int(5 * FS))
        fragmento_retrasado = np.concatenate((retraso, fragmento_amplificado))

        # Graficar ambas señales
        tiempo_original = np.linspace(0, duracion, len(fragmento_original))
        tiempo_modificado = np.linspace(0, duracion + 5, len(fragmento_retrasado))

        plt.figure(figsize=(10, 4))

        # Señal original
        plt.subplot(1, 2, 1)
        plt.stem(tiempo_original, fragmento_original, linefmt='b-', markerfmt='bo', basefmt='r-')
        plt.title("Fragmento Original")
        plt.xlabel("Tiempo (s)")
        plt.ylabel("Amplitud")

        # Señal modificada
        plt.subplot(1, 2, 2)
        plt.stem(tiempo_modificado, fragmento_retrasado, linefmt='g-', markerfmt='go', basefmt='r-')
        plt.title("Escalado y Retrasado")
        plt.xlabel("Tiempo (s)")
        plt.ylabel("Amplitud")

        plt.tight_layout()

        # Guardar la imagen en memoria y convertirla a base64
        img_io = io.BytesIO()
        plt.savefig(img_io, format='png')
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
        plt.close()

        # Guardar el nuevo audio modificado para reproducirlo
        sf.write('./static/audio_modificado.wav', fragmento_retrasado, FS)

        return render_template('procesar_audio.html', audio_url=url_for('static', filename='audio_modificado.wav'),
                               img_base64=img_base64)

    return render_template('procesar_audio.html')

if __name__ == '__main__':
    app.run(debug=True)