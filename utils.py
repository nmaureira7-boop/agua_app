def obtener_ingreso_usuario(usuario_id, conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, direccion, consumo, TO_CHAR(fecha, 'YYYY-MM-DD')
        FROM ingresos_agua
        WHERE usuario_id = :1
        FETCH FIRST 1 ROWS ONLY
    """, [usuario_id])
    ingreso = cursor.fetchone()
    cursor.close()
    return ingreso
def validar_consumo(valor):
    try:
        consumo = float(valor)
        if consumo < 0:
            raise ValueError("Consumo negativo")
        return consumo
    except (ValueError, TypeError):
        return None