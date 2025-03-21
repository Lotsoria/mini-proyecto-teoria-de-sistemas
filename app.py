from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from scipy.io import wavfile
from scipy.signal import resample, butter, lfilter
import sounddevice as sd
import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
import matplotlib



matplotlib.use('Agg') 

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
        
# Función para aplicar un filtro pasa-bajos (bajos al lado izquierdo)
def lowpass_filter(data, cutoff, fs, order=5):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return lfilter(b, a, data)

# Función para aplicar un filtro pasa-altos (altos al lado derecho)
def highpass_filter(data, cutoff, fs, order=5):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return lfilter(b, a, data)

# Función para convertir mono a estéreo separando bajos y altos
def make_stereo_with_freq_split(input_file, output_file, cutoff=1000):
    """Convierte un archivo mono a estéreo separando bajos (izquierda) y altos (derecha)"""
    
    # Leer el archivo de audio
    x, FS = sf.read(input_file, dtype='float32')

    # Verificar si el archivo es mono
    if len(x.shape) > 1:
        print("El archivo ya es estéreo.")
        return

    # Aplicar filtros
    left_channel = lowpass_filter(x, cutoff, FS)  # Bajos al canal izquierdo
    right_channel = highpass_filter(x, cutoff, FS)  # Altos al canal derecho

    # Crear el nuevo audio estéreo combinando ambos canales
    x_stereo = np.column_stack((left_channel, right_channel))

    # Guardar el nuevo archivo estéreo
    sf.write(output_file, x_stereo, FS)
    print(f"Archivo estéreo generado con bajos a la izquierda y altos a la derecha: {output_file}");

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
    elif opcion == 6:
        return redirect(url_for('intercambio_canales'))

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
        try:
            x, FS = sf.read('./static/Happy - Mono2.wav', dtype='float32')
            inicio = 10  
            duracion = 5 

            inicio_muestras = int(inicio * FS)
            fin_muestras = int((inicio + duracion) * FS)
            fragmento_original = x[inicio_muestras:fin_muestras]

            fragmento_amplificado = 1.5 * fragmento_original

            retraso = np.zeros(int(5 * FS))
            fragmento_retrasado = np.concatenate((retraso, fragmento_amplificado))

            plt.close('all')
            
            tiempo_original = np.linspace(0, duracion, len(fragmento_original))
            tiempo_modificado = np.linspace(0, duracion + 5, len(fragmento_retrasado))

            plt.figure(figsize=(10, 4))
            
            plt.subplot(1, 2, 1)
            plt.stem(tiempo_original[::50], fragmento_original[::50], linefmt='b-', markerfmt='bo', basefmt='r-')
            plt.title("Fragmento Original")
            plt.xlabel("Tiempo (s)")
            plt.ylabel("Amplitud")
            
            plt.subplot(1, 2, 2)
            plt.stem(tiempo_modificado[::50], fragmento_retrasado[::50], linefmt='g-', markerfmt='go', basefmt='r-')
            plt.title("Escalado y Retrasado")
            plt.xlabel("Tiempo (s)")
            plt.ylabel("Amplitud")
            
            plt.tight_layout()

            img_io = io.BytesIO()
            plt.savefig(img_io, format='png')
            img_io.seek(0)
            img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
            plt.close()

            sf.write('./static/audio_modificado.wav', fragmento_retrasado.astype(np.float32), FS)

            print(f"Longitud de la imagen base64: {len(img_base64)}")

            # reproducir(fragmento_retrasado, FS)

            return render_template('procesar_audio.html', audio_url=url_for('static', filename='audio_modificado.wav'),
                                img_base64=img_base64)
        except Exception as e:
            print(f"Error procesando el audio: {e}")
            return render_template('procesar_audio.html', error=str(e))
    return render_template('procesar_audio.html')

@app.route('/intercambio_canales', methods=['GET', 'POST'])
def intercambio_canales():
    timestamp = int(datetime.now().timestamp())
    if request.method == 'POST':
        try:
            archivo_entrada = "./static/Happy - Mono2.wav"  # Asegúrate de que este sea el nombre correcto
            archivo_salida = "./static/audio_stereo.wav"  # Nombre del nuevo archivo estéreo

            x, FS = sf.read(archivo_entrada, dtype='float32')
            if len(x.shape) == 1:
                print("El archivo es mono, convirtiéndolo a estéreo...")
                # x_stereo = np.column_stack((x, x)) 
                make_stereo_with_freq_split(archivo_entrada, archivo_salida)
                x_stereo, FS = sf.read(archivo_salida, dtype='float32')
                print(len(x_stereo.shape))
                
            opcion = request.form['opcion']
            print("Opcion",opcion)
            if opcion == '1':
                inicio = 0  
                duracion = 5
                inicio_muestra = int(inicio * FS)
                fin_muestra = int((inicio + duracion) * FS)
                x_recortado = x_stereo[inicio_muestra:fin_muestra]
                sf.write(archivo_salida, x_recortado, FS)
                return render_template('intercambiar_canales.html', audio_url=archivo_salida, timestamp=timestamp)
            elif opcion == '2':
                x_intercambiado = np.copy(x_stereo)
                x_intercambiado[:, [0, 1]] = x_stereo[:, [1, 0]]
                sf.write(archivo_salida, x_intercambiado, FS)
                return render_template('intercambiar_canales.html', audio_url=archivo_salida, timestamp=timestamp)

        except Exception as e:
            print(f"Error en intercambio de canales: {e}")
            return render_template('intercambiar_canales.html', error=str(e))
    return render_template('intercambiar_canales.html')


if __name__ == '__main__':
    app.run(debug=True)