# Librerías estándar
import os
import io
import calendar
from collections import defaultdict
from statistics import mean
from datetime import date

# Librerías externas
import pandas as pd
import oracledb
from flask import Flask, render_template, request, redirect, session, flash, send_file, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from PIL import Image  # solo si realmente lo usas

# Módulos propios
from db_config import get_connection
from utils import obtener_ingreso_usuario, validar_consumo


app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # Necesaria para usar sesiones y flash

load_dotenv()
print("Usuario:", os.getenv("DB_USER"))

app = Flask(__name__)
app.secret_key = 'clave_segura'

@app.route('/introduccion')
def introduccion():
    return render_template('introduccion.html')

@app.template_filter('month_name')
def month_name_filter(mes_num):
    return calendar.month_name[int(mes_num)]

@app.route('/')
def home():
    return redirect('/introduccion')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo'].lower()
        direccion = request.form['direccion']
        contraseña = request.form['contraseña']
        confirmar = request.form['confirmar_contraseña']

        # Validar que las contraseñas coincidan
        if contraseña != confirmar:
            flash("⚠️ Las contraseñas no coinciden.", "warning")
            return redirect('/registro')

        contraseña_hash = generate_password_hash(contraseña)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE correo = :1", [correo])
        existente = cursor.fetchone()

        if existente:
            flash("⚠️ El correo ya está registrado.", "warning")
            cursor.close()
            conn.close()
            return redirect('/registro')

        cursor.execute("""
            INSERT INTO usuarios (nombre, correo, contraseña, direccion)
            VALUES (:1, :2, :3, :4)
        """, [nombre, correo, contraseña_hash, direccion])

        conn.commit()
        cursor.close()
        conn.close()
        flash("🎉 ¡Cuenta creada exitosamente!", "success")
        return redirect('/login')

    return render_template('base.html', vista='registro')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo'].lower()
        contraseña = request.form['contraseña']

        conn = get_connection()
        cursor = conn.cursor()

        # 🔍 Incluye el campo 'rol' en la consulta
        cursor.execute("SELECT id, contraseña, rol FROM usuarios WHERE correo = :1", [correo])
        usuario = cursor.fetchone()

        cursor.close()
        conn.close()

        if usuario and check_password_hash(usuario[1], contraseña):
            session['usuario_id'] = usuario[0]
            session['usuario_rol'] = usuario[2]  # ✅ Guarda el rol en sesión
            flash("Inicio de sesión exitoso. ¡Bienvenido!", "success")
            return redirect('/ingreso')
        else:
            flash("Correo o contraseña incorrectos", "error")
            return redirect('/login')

    return render_template('base.html', vista='login')

@app.route('/logout')
def logout():
    session.clear()
    flash("👋 Has cerrado sesión correctamente.", "success")
    return redirect('/login')

from datetime import datetime
from flask import render_template, request, redirect, session, flash
from db_config import get_connection
from utils import validar_consumo, obtener_ingreso_usuario

from werkzeug.utils import secure_filename
import cv2
import pytesseract
import re
import os

@app.route('/ingreso', methods=['GET', 'POST'])
def ingreso():
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()

    # ✅ Obtener dirección actual del usuario
    cursor.execute("SELECT direccion FROM usuarios WHERE id = :1", [session['usuario_id']])
    resultado_direccion = cursor.fetchone()
    direccion_usuario = resultado_direccion[0] if resultado_direccion and resultado_direccion[0] else ''

    # ✅ Fecha actual
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')

    # ✅ Verificar si ya se registró una lectura hoy
    cursor.execute("""
        SELECT COUNT(*) FROM ingresos_agua
        WHERE usuario_id = :1 AND TO_CHAR(fecha, 'YYYY-MM-DD') = :2
    """, [session['usuario_id'], fecha_hoy])
    lecturas_hoy = cursor.fetchone()[0]
    mostrar_advertencia = lecturas_hoy > 0

    if request.method == 'POST':
        try:
            lectura_actual = int(request.form.get('lectura_m3'))
        except (TypeError, ValueError):
            flash("⚠️ La lectura ingresada no es válida.", "error")
            cursor.close()
            conn.close()
            return redirect('/ingreso')

        # ✅ Obtener última lectura anterior
        cursor.execute("""
            SELECT lectura_m3 FROM ingresos_agua
            WHERE usuario_id = :1
            ORDER BY fecha DESC FETCH FIRST 1 ROWS ONLY
        """, [session['usuario_id']])
        resultado = cursor.fetchone()
        lectura_anterior = resultado[0] if resultado and resultado[0] is not None else 0

        consumo = lectura_actual
        if consumo <= 0:
            flash("⚠️ La lectura ingresada es menor a la anterior.", "warning")
            cursor.close()
            conn.close()
            return redirect('/ingreso')

        # ✅ Calcular monto escalonado
        monto = calcular_pago_escalonado(consumo)

        # ✅ Dirección ingresada (si se modificó)
        direccion_form = request.form.get('direccion1') or direccion_usuario

        # ✅ Procesar fotografía (solo guardar archivo)
        foto = request.files.get('foto')
        nombre_foto = None
        if foto and foto.filename != '':
            upload_folder = os.path.join("uploads", "lecturas")
            os.makedirs(upload_folder, exist_ok=True)

            nombre_foto = f"{session['usuario_id']}_{fecha_hoy}_{secure_filename(foto.filename)}"
            ruta_foto = os.path.join(upload_folder, nombre_foto)
            foto.save(ruta_foto)

        # ✅ Insertar ingreso con lectura, consumo, monto y foto
        cursor.execute("""
            INSERT INTO ingresos_agua (usuario_id, lectura_m3, consumo, monto, fecha, foto)
            VALUES (:1, :2, :3, :4, TO_DATE(:5, 'YYYY-MM-DD'), :6)
        """, [session['usuario_id'], lectura_actual, consumo, monto, fecha_hoy, nombre_foto])

        # ✅ Actualizar dirección si cambió
        if direccion_form != direccion_usuario:
            cursor.execute("""
                UPDATE usuarios SET direccion = :1 WHERE id = :2
            """, [direccion_form, session['usuario_id']])
            direccion_usuario = direccion_form

        conn.commit()
        cursor.close()
        conn.close()
        return redirect('/pago')

    cursor.close()
    conn.close()
    return render_template(
        'base.html',
        vista='ingreso',
        ingreso_existente=None,
        direccion_usuario=direccion_usuario,
        fecha_actual=fecha_hoy,
        lectura_hoy=mostrar_advertencia
    )
@app.route("/resumen", methods=["GET", "POST"])
def resumen():
    if "usuario_id" not in session:
        return redirect("/login")

    from datetime import datetime
    import calendar
    from collections import defaultdict

    hoy = datetime.now()
    conn = get_connection()
    cursor = conn.cursor()

    # Filtros
    anio = int(request.form.get("año")) if request.method == "POST" and request.form.get("año") else None
    mes = int(request.form.get("mes")) if request.method == "POST" and request.form.get("mes") else None

    # Años disponibles
    cursor.execute("""
        SELECT DISTINCT EXTRACT(YEAR FROM fecha)
        FROM ingresos_agua
        WHERE usuario_id = :1
        ORDER BY 1 DESC
    """, [session["usuario_id"]])
    años_disponibles = [int(f[0]) for f in cursor.fetchall()]

    labels_mensual, valores_mensual = [], []
    labels_anual, valores_anual = [], []

    if anio and mes:
        # Gráfico mensual: consumo diario en ese mes y año
        cursor.execute("""
            SELECT TO_CHAR(fecha, 'DD'), SUM(consumo)
            FROM ingresos_agua
            WHERE usuario_id = :1 AND EXTRACT(YEAR FROM fecha) = :2 AND EXTRACT(MONTH FROM fecha) = :3
            GROUP BY TO_CHAR(fecha, 'DD')
            ORDER BY TO_CHAR(fecha, 'DD')
        """, [session["usuario_id"], anio, mes])
        datos = cursor.fetchall()
        labels_mensual = [str(int(d[0])) for d in datos]
        valores_mensual = [float(d[1]) for d in datos]

    elif anio and not mes:
        # Gráfico anual: consumo por mes en ese año
        cursor.execute("""
            SELECT EXTRACT(MONTH FROM fecha), SUM(consumo)
            FROM ingresos_agua
            WHERE usuario_id = :1 AND EXTRACT(YEAR FROM fecha) = :2
            GROUP BY EXTRACT(MONTH FROM fecha)
            ORDER BY 1
        """, [session["usuario_id"], anio])
        datos = cursor.fetchall()
        labels_anual = [calendar.month_name[int(d[0])] for d in datos]
        valores_anual = [float(d[1]) for d in datos]

    elif mes and not anio:
        # Gráfico anual: consumo de ese mes a lo largo de los años
        cursor.execute("""
            SELECT EXTRACT(YEAR FROM fecha), SUM(consumo)
            FROM ingresos_agua
            WHERE usuario_id = :1 AND EXTRACT(MONTH FROM fecha) = :2
            GROUP BY EXTRACT(YEAR FROM fecha)
            ORDER BY 1
        """, [session["usuario_id"], mes])
        datos = cursor.fetchall()
        labels_anual = [str(int(d[0])) for d in datos]
        valores_anual = [float(d[1]) for d in datos]

    else:
        # Sin filtros: gráfico anual del mes actual
        cursor.execute("""
            SELECT EXTRACT(YEAR FROM fecha), SUM(consumo)
            FROM ingresos_agua
            WHERE usuario_id = :1 AND EXTRACT(MONTH FROM fecha) = :2
            GROUP BY EXTRACT(YEAR FROM fecha)
            ORDER BY 1
        """, [session["usuario_id"], hoy.month])
        datos = cursor.fetchall()
        labels_anual = [str(int(d[0])) for d in datos]
        valores_anual = [float(d[1]) for d in datos]
        mes = hoy.month

    # ✅ Lecturas con foto agrupadas por mes
    cursor.execute("""
        SELECT TO_CHAR(fecha, 'YYYY-MM-DD'), consumo, monto, foto
        FROM ingresos_agua
        WHERE usuario_id = :1
        ORDER BY fecha DESC
    """, [session["usuario_id"]])
    resultados = cursor.fetchall()

    lecturas_por_mes = defaultdict(list)
    for fecha_str, consumo, monto, foto in resultados:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        mes_key = fecha.strftime("%B %Y")  # Ej: "Noviembre 2025"
        lecturas_por_mes[mes_key].append({
            "fecha": fecha_str,
            "consumo": consumo,
            "monto": monto,
            "foto": foto
        })

    if not labels_mensual and not labels_anual:
        flash("No hay datos para el filtro seleccionado.", "warning")

    cursor.close()
    conn.close()

    return render_template(
        "base.html",
        vista="resumen",
        año_seleccionado=anio,
        mes_seleccionado=mes,
        años_disponibles=años_disponibles,
        labels_mensual=labels_mensual,
        valores_mensual=valores_mensual,
        labels_anual=labels_anual,
        valores_anual=valores_anual,
        lecturas_por_mes=lecturas_por_mes
    )
@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT TO_CHAR(fecha, 'DD'), consumo, fecha
        FROM ingresos_agua
        WHERE usuario_id = :1
        ORDER BY fecha
    """, [session['usuario_id']])
    registros = cursor.fetchall()
    cursor.close()
    conn.close()

    hoy = date.today()
    dias = defaultdict(list)
    futuros = {}

    for dia_str, consumo, fecha in registros:
        dia = int(dia_str)
        consumo = float(consumo)
        dias[dia].append(consumo)
        if fecha.date() > hoy:
            futuros[dia] = consumo  # último ingreso futuro por día

    labels_dias = sorted(dias.keys())
    valores_promedio = [round(mean(dias[d]), 2) for d in labels_dias]
    valores_futuros = [futuros.get(d, None) for d in labels_dias]

    return render_template(
        'base.html',
        vista='dashboard',
        labels_dias=labels_dias,
        valores_promedio=valores_promedio,
        valores_futuros=valores_futuros
    )


@app.route('/pago', methods=['GET', 'POST'])
def pago():
    if 'usuario_id' not in session:
        return redirect('/login')

    fecha_actual = datetime.now()
    mes_actual = fecha_actual.month
    anio_actual = fecha_actual.year

    conn = get_connection()
    cursor = conn.cursor()

    # 🔍 Buscar el último ingreso del mes que no ha sido pagado, incluyendo monto y dirección
    cursor.execute("""
        SELECT i.id, i.consumo, i.monto, u.direccion, TO_CHAR(i.fecha, 'YYYY-MM-DD')
        FROM ingresos_agua i
        JOIN usuarios u ON i.usuario_id = u.id
        WHERE i.usuario_id = :1
          AND EXTRACT(MONTH FROM i.fecha) = :2
          AND EXTRACT(YEAR FROM i.fecha) = :3
          AND NOT EXISTS (
              SELECT 1 FROM pagos_agua p WHERE p.ingreso_id = i.id
          )
        ORDER BY i.fecha DESC
        FETCH FIRST 1 ROWS ONLY
    """, [session['usuario_id'], mes_actual, anio_actual])
    resultado = cursor.fetchone()

    if not resultado:
        flash("✅ Ya has pagado todas las lecturas de este mes.", "info")
        cursor.close()
        conn.close()
        return redirect('/historial_pagos')

    ingreso_id = resultado[0]
    consumo_m3 = resultado[1]
    monto_total = resultado[2]
    direccion = resultado[3]
    fecha_lectura = resultado[4]

    # 📋 Obtener resumen de ingresos (pagados y pendientes)
    cursor.execute("""
        SELECT i.id, TO_CHAR(i.fecha, 'YYYY-MM-DD') AS fecha, u.direccion, i.consumo,
               CASE WHEN p.id IS NOT NULL THEN 'pagado' ELSE 'pendiente' END AS estado,
               p.monto
        FROM ingresos_agua i
        JOIN usuarios u ON i.usuario_id = u.id
        LEFT JOIN pagos_agua p ON p.ingreso_id = i.id
        WHERE i.usuario_id = :1
        ORDER BY i.fecha DESC
    """, [session['usuario_id']])
    resumen = cursor.fetchall()
    resumen_ingresos = [
        {
            'fecha': row[1],
            'direccion': row[2],
            'consumo': row[3],
            'estado': row[4],
            'monto': row[5] if row[5] else None
        }
        for row in resumen
    ]

    if request.method == 'POST':
        # 💳 Registrar el pago vinculado al ingreso
        cursor.execute("""
            INSERT INTO pagos_agua (usuario_id, ingreso_id, consumo, monto, fecha_pago)
            VALUES (:1, :2, :3, :4, TO_DATE(:5, 'YYYY-MM-DD'))
        """, [session['usuario_id'], ingreso_id, consumo_m3, monto_total, fecha_lectura])
        conn.commit()
        flash("✅ Pago registrado correctamente.", "success")
        cursor.close()
        conn.close()
        return redirect('/historial_pagos')

    cursor.close()
    conn.close()
    return render_template(
        'base.html',
        vista='pago',
        monto=monto_total,
        consumo=consumo_m3,
        direccion=direccion,
        fecha=fecha_lectura,
        resumen_ingresos=resumen_ingresos
    )
@app.route('/editar_ingreso', methods=['GET', 'POST'])
def editar_ingreso_manual():
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()

    # Buscar ingreso existente
    cursor.execute("""
        SELECT id, direccion, consumo, TO_CHAR(fecha, 'YYYY-MM-DD')
        FROM ingresos_agua
        WHERE usuario_id = :1
        FETCH FIRST 1 ROWS ONLY
    """, [session['usuario_id']])
    ingreso = cursor.fetchone()

    if not ingreso:
        cursor.close()
        conn.close()
        flash("No tienes ningún ingreso registrado para editar.", "warning")
        return redirect('/ingreso')

    if request.method == 'POST':
        direccion = request.form.get('direccion')
        consumo = request.form.get('consumo')
        fecha = request.form.get('fecha')

        if direccion and consumo and fecha:
            try:
                consumo = float(consumo)
                if consumo < 0:
                    raise ValueError("Consumo negativo")
            except (ValueError, TypeError):
                flash("⚠️ El consumo debe ser un número válido y positivo.", "error")
                return redirect('/editar_ingreso')

            cursor.execute("""
                UPDATE ingresos_agua
                SET direccion = :1, consumo = :2, fecha = TO_DATE(:3, 'YYYY-MM-DD')
                WHERE id = :4 AND usuario_id = :5
            """, [direccion, consumo, fecha, ingreso[0], session['usuario_id']])
            conn.commit()
            flash("Ingreso actualizado correctamente.", "success")
            return redirect('/ingreso')

    cursor.close()
    conn.close()
    return render_template('base.html', vista='editar_ingreso', ingreso=ingreso)
@app.route('/eliminar_ingreso/<int:ingreso_id>', methods=['POST'])
def eliminar_ingreso(ingreso_id):
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM ingresos_agua
        WHERE id = :1 AND usuario_id = :2
    """, [ingreso_id, session['usuario_id']])
    conn.commit()
    cursor.close()
    conn.close()

    flash("Ingreso eliminado correctamente.", "success")
    return redirect('/ingreso')

@app.route('/historial_pagos')
def historial_pagos():
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TO_CHAR(fecha_pago, 'YYYY-MM-DD'), consumo, monto
        FROM pagos_agua
        WHERE usuario_id = :1
        ORDER BY fecha_pago DESC
    """, [session['usuario_id']])
    pagos = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('base.html', vista='historial_pagos', pagos=pagos)
@app.route('/limpiar_historial_pagos', methods=['POST'])
def limpiar_historial_pagos():
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Obtener los ingreso_id que fueron pagados
    cursor.execute("""
        SELECT ingreso_id
        FROM pagos_agua
        WHERE usuario_id = :usuario_id
    """, {'usuario_id': session['usuario_id']})
    ingresos_pagados = [row[0] for row in cursor.fetchall()]

    # 2. Eliminar los pagos
    cursor.execute("""
        DELETE FROM pagos_agua
        WHERE usuario_id = :usuario_id
    """, {'usuario_id': session['usuario_id']})

    # 3. Eliminar los ingresos asociados
    if ingresos_pagados:
        # Construir lista de parámetros :id0, :id1, ...
        ids_bind = ', '.join([f":id{i}" for i in range(len(ingresos_pagados))])
        query = f"DELETE FROM ingresos_agua WHERE id IN ({ids_bind})"
        bind_dict = {f"id{i}": ingreso_id for i, ingreso_id in enumerate(ingresos_pagados)}
        cursor.execute(query, bind_dict)

    conn.commit()
    cursor.close()
    conn.close()

    flash("🧹 Historial de pagos y sus ingresos asociados fueron eliminados correctamente.", "success")
    return redirect('/historial_pagos')
print(app.url_map)
@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()

    # Obtener datos actuales del usuario
    cursor.execute("""
        SELECT nombre, apellido, correo, direccion FROM usuarios WHERE id = :1
    """, [session['usuario_id']])
    usuario = cursor.fetchone()

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        direccion = request.form.get('direccion')
        nueva_contraseña = request.form.get('nueva_contraseña')
        confirmar = request.form.get('confirmar_contraseña')

        # Validar que las contraseñas coincidan si se ingresó una nueva
        if nueva_contraseña:
            if nueva_contraseña != confirmar:
                flash("⚠️ Las contraseñas no coinciden.", "warning")
                cursor.close()
                conn.close()
                return redirect('/perfil')
            else:
                hash = generate_password_hash(nueva_contraseña)
                cursor.execute("UPDATE usuarios SET contraseña = :1 WHERE id = :2", [hash, session['usuario_id']])

        # Actualizar datos generales
        cursor.execute("""
            UPDATE usuarios SET nombre = :1, apellido = :2, direccion = :3 WHERE id = :4
        """, [nombre, apellido, direccion, session['usuario_id']])

        conn.commit()
        flash("✅ Perfil actualizado correctamente.", "success")
        return redirect('/perfil')

    cursor.close()
    conn.close()
    return render_template('base.html', vista='perfil', usuario=usuario)

def obtener_tarifas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT desde, hasta, precio FROM tarifas ORDER BY desde ASC")
    tarifas = cursor.fetchall()
    cursor.close()
    conn.close()
    return tarifas

def calcular_pago_escalonado(consumo_m3):
    tarifas = obtener_tarifas()
    total = 0
    restante = consumo_m3

    for desde, hasta, precio in tarifas:
        if restante <= 0:
            break

        if hasta is not None:
            tramo_m3 = hasta - desde 
        else:
            tramo_m3 = restante  # tramo infinito, solo lo que queda

        cantidad = min(restante, tramo_m3)
        total += cantidad * precio
        restante -= cantidad

    return total
@app.route('/admin/tarifas', methods=['GET', 'POST'])
def administrar_tarifas():
    if session.get('usuario_rol') != 'admin':
        flash("⚠️ Acceso restringido solo para administradores.", "warning")
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()

    # ✅ Agregar nuevo tramo
    if request.method == 'POST':
        try:
            desde = int(request.form['desde'])
            hasta = request.form['hasta']
            precio = int(request.form['precio'])

            hasta_valor = None if hasta.strip() == '' else int(hasta)

            cursor.execute("""
                INSERT INTO tarifas (id, desde, hasta, precio)
                VALUES (tarifas_seq.NEXTVAL, :1, :2, :3)
            """, [desde, hasta_valor, precio])
            conn.commit()
            flash("✅ Tramo agregado correctamente.", "success")
        except Exception as e:
            flash(f"❌ Error al agregar tramo: {e}", "danger")

    # ✅ Mostrar tramos actuales
    cursor.execute("SELECT id, desde, hasta, precio FROM tarifas ORDER BY desde ASC")
    tramos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('base.html', vista='admin_tarifas', tramos=tramos)

@app.route('/admin/tarifas/eliminar/<int:tramo_id>', methods=['POST'])
def eliminar_tramo(tramo_id):
    if session.get('usuario_rol') != 'admin':
        flash("⚠️ Acceso restringido.", "warning")
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tarifas WHERE id = :1", [tramo_id])
    conn.commit()
    cursor.close()
    conn.close()

    flash("🗑️ Tramo eliminado correctamente.", "success")
    return redirect('/admin/tarifas')

@app.route('/admin/tarifas/editar/<int:tramo_id>', methods=['POST'])
def editar_tramo(tramo_id):
    if session.get('usuario_rol') != 'admin':
        flash("⚠️ Acceso restringido.", "warning")
        return redirect('/')

    try:
        desde = int(request.form['desde'])
        hasta = request.form['hasta']
        precio = int(request.form['precio'])
        hasta_valor = None if hasta.strip() == '' else int(hasta)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tarifas
            SET desde = :1, hasta = :2, precio = :3
            WHERE id = :4
        """, [desde, hasta_valor, precio, tramo_id])
        conn.commit()
        cursor.close()
        conn.close()

        flash("✅ Tramo actualizado correctamente.", "success")
    except Exception as e:
        flash(f"❌ Error al actualizar tramo: {e}", "danger")

    return redirect('/admin/tarifas')

@app.route('/ingreso/editar_formulario/<int:ingreso_id>')
def mostrar_formulario_edicion(ingreso_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, direccion, consumo, TO_CHAR(fecha, 'YYYY-MM-DD') FROM ingresos_agua WHERE id = :1", [ingreso_id])
    ingreso = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('editar_ingreso.html', ingreso=ingreso)

@app.route('/prueba')
def prueba():
    return "Ruta de prueba activa"
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'usuario_id' not in session or session.get('usuario_rol') != 'admin':
        flash("⚠️ Acceso restringido a administradores.", "error")
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()

    # ✅ Obtener todos los ingresos con datos de usuario
    cursor.execute("""
        SELECT u.id, u.nombre, u.correo, u.direccion,
               i.id, i.fecha, i.lectura_m3, i.consumo, i.monto, i.foto, i.estado_validacion
        FROM ingresos_agua i
        LEFT JOIN usuarios u ON i.usuario_id = u.id
        ORDER BY i.fecha DESC
    """)
    registros = cursor.fetchall()
    cursor.close()
    conn.close()

    # Convertir a lista de diccionarios para la vista
    ingresos = [
        {
            "usuario_id": row[0],
            "nombre": row[1],
            "correo": row[2],
            "direccion": row[3],
            "ingreso_id": row[4],
            "fecha": row[5],
            "lectura": row[6],
            "consumo": row[7],
            "monto": row[8],
            "foto": row[9],
            "estado": row[10]
        }
        for row in registros
    ]

    return render_template('vistas/admin_dashboard.html', ingresos=ingresos)

@app.route('/admin/export')
def admin_export():
    if 'usuario_id' not in session or session.get('usuario_rol') != 'admin':
        flash("⚠️ Acceso restringido a administradores.", "error")
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.nombre, u.correo, u.direccion,
               i.fecha, i.lectura_m3, i.consumo, i.monto, i.foto
        FROM ingresos_agua i
        JOIN usuarios u ON i.usuario_id = u.id
        ORDER BY i.fecha DESC
    """)
    registros = cursor.fetchall()
    cursor.close()
    conn.close()

    # Crear DataFrame
    df = pd.DataFrame(registros, columns=[
        "Nombre", "Correo", "Dirección", "Fecha", "Lectura (m³)", "Consumo", "Monto", "Foto"
    ])

    # Exportar a Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Ingresos")
    output.seek(0)

    return send_file(output, download_name="ingresos_admin.xlsx", as_attachment=True)

@app.route('/admin/editar_ingreso/<int:ingreso_id>', methods=['GET', 'POST'])
def admin_editar_ingreso(ingreso_id):
    # Validar acceso de administrador
    if 'usuario_id' not in session or session.get('usuario_rol') != 'admin':
        flash("⚠️ Acceso restringido a administradores.", "error")
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()

    # Obtener ingreso específico
    cursor.execute("""
        SELECT i.id, u.nombre, u.correo, u.direccion, 
               i.consumo, TO_CHAR(i.fecha, 'YYYY-MM-DD'), 
               i.foto, i.estado_validacion
        FROM ingresos_agua i
        JOIN usuarios u ON i.usuario_id = u.id
        WHERE i.id = :1
    """, [ingreso_id])
    row = cursor.fetchone()

    if not row:
        cursor.close()
        conn.close()
        flash("Ingreso no encontrado.", "warning")
        return redirect('/admin/dashboard')

    # Convertir tuple en diccionario para usar en el template
    ingreso = {
        "ingreso_id": row[0],
        "nombre": row[1],
        "correo": row[2],
        "direccion": row[3],
        "consumo": row[4],
        "fecha": row[5],
        "foto": row[6],
        "estado": row[7]
    }

    if request.method == 'POST':
        estado = request.form.get('estado')  # "aprobado" o "rechazado"
        cursor.execute("""
            UPDATE ingresos_agua
            SET estado_validacion = :1
            WHERE id = :2
        """, [estado, ingreso_id])
        conn.commit()
        cursor.close()
        conn.close()
        flash("✅ Estado de ingreso actualizado.", "success")
        return redirect('/admin/dashboard')

    cursor.close()
    conn.close()
    return render_template('vistas/admin_editar_ingreso.html', ingreso=ingreso)

@app.route('/admin/eliminar_ingreso/<int:ingreso_id>', methods=['POST'])
def admin_eliminar_ingreso(ingreso_id):
    if 'usuario_id' not in session or session.get('usuario_rol') != 'admin':
        flash("⚠️ Acceso restringido a administradores.", "error")
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ingresos_agua WHERE id = :1", [ingreso_id])
    conn.commit()
    cursor.close()
    conn.close()

    flash("✅ Ingreso eliminado.", "success")
    return redirect('/admin/dashboard')

if __name__ == '__main__':
    app.run(debug=True)
