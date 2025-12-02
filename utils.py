def obtener_ingreso_usuario(usuario_id, conn, ultimo=True):
    """
    Obtiene el ingreso de un usuario.
    - Si ultimo=True, devuelve el último ingreso registrado.
    - Si ultimo=False, devuelve todos los ingresos.
    """
    cursor = conn.cursor()
    if ultimo:
        cursor.execute("""
            SELECT id, direccion, consumo, TO_CHAR(fecha, 'YYYY-MM-DD')
            FROM ingresos_agua
            WHERE usuario_id = :1
            ORDER BY fecha DESC
            FETCH FIRST 1 ROWS ONLY
        """, [usuario_id])
        ingreso = cursor.fetchone()
        cursor.close()
        return ingreso
    else:
        cursor.execute("""
            SELECT id, direccion, consumo, TO_CHAR(fecha, 'YYYY-MM-DD')
            FROM ingresos_agua
            WHERE usuario_id = :1
            ORDER BY fecha DESC
        """, [usuario_id])
        ingresos = cursor.fetchall()
        cursor.close()
        return ingresos


def validar_consumo(valor):
    """
    Valida que el consumo sea un número positivo.
    Devuelve el consumo como float si es válido, o None si no lo es.
    """
    try:
        consumo = float(valor)
        if consumo < 0:
            raise ValueError("Consumo negativo")
        return consumo
    except (ValueError, TypeError):
        return None
