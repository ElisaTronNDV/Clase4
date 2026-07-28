def _crear_producto(db_session, **overrides):
    from app.models.producto import Producto

    datos = dict(
        material="SAE_1010",
        espesor_mm=2.1,
        largo_mm=1200.0,
        ancho_mm=600.0,
        stock_fisico=10.0,
        stock_comprometido=0.0,
        punto_pedido=2.0,
    )
    datos.update(overrides)
    producto = Producto(**datos)
    db_session.add(producto)
    db_session.commit()
    db_session.refresh(producto)
    return producto


def test_coincidencia_exacta(db_session):
    from app.services.stock import buscar_producto_coincidente

    producto = _crear_producto(db_session)

    encontrado = buscar_producto_coincidente(
        db_session,
        material="SAE_1010",
        espesor_mm=2.1,
        largo_mm=1200.0,
        ancho_mm=600.0,
        margen_tolerancia_mm=1.0,
    )
    assert encontrado is not None
    assert encontrado.id == producto.id


def test_coincidencia_dentro_de_tolerancia(db_session):
    from app.services.stock import buscar_producto_coincidente

    producto = _crear_producto(db_session, largo_mm=1200.7, ancho_mm=600.4)

    encontrado = buscar_producto_coincidente(
        db_session,
        material="SAE_1010",
        espesor_mm=2.1,
        largo_mm=1200.0,
        ancho_mm=600.0,
        margen_tolerancia_mm=1.0,
    )
    assert encontrado is not None
    assert encontrado.id == producto.id


def test_sin_coincidencia_fuera_de_tolerancia(db_session):
    from app.services.stock import buscar_producto_coincidente

    _crear_producto(db_session, largo_mm=1202.0, ancho_mm=600.0)

    encontrado = buscar_producto_coincidente(
        db_session,
        material="SAE_1010",
        espesor_mm=2.1,
        largo_mm=1200.0,
        ancho_mm=600.0,
        margen_tolerancia_mm=1.0,
    )
    assert encontrado is None


def test_material_distinto_no_matchea_aunque_dimensiones_sean_exactas(db_session):
    from app.services.stock import buscar_producto_coincidente

    _crear_producto(db_session, material="INOX")

    encontrado = buscar_producto_coincidente(
        db_session,
        material="SAE_1010",
        espesor_mm=2.1,
        largo_mm=1200.0,
        ancho_mm=600.0,
        margen_tolerancia_mm=1.0,
    )
    assert encontrado is None


def test_espesor_distinto_no_matchea_aunque_dimensiones_sean_exactas(db_session):
    from app.services.stock import buscar_producto_coincidente

    _crear_producto(db_session, espesor_mm=3.0)

    encontrado = buscar_producto_coincidente(
        db_session,
        material="SAE_1010",
        espesor_mm=2.1,
        largo_mm=1200.0,
        ancho_mm=600.0,
        margen_tolerancia_mm=1.0,
    )
    assert encontrado is None


def test_desempate_por_menor_id_en_empate_exacto_de_diferencia(db_session):
    from app.services.stock import buscar_producto_coincidente

    # Ambos a distancia total 0.5 del objetivo (1200, 600); A se crea primero (id menor).
    producto_a = _crear_producto(db_session, largo_mm=1200.5, ancho_mm=600.0)
    _crear_producto(db_session, largo_mm=1200.0, ancho_mm=600.5)

    encontrado = buscar_producto_coincidente(
        db_session,
        material="SAE_1010",
        espesor_mm=2.1,
        largo_mm=1200.0,
        ancho_mm=600.0,
        margen_tolerancia_mm=1.0,
    )
    assert encontrado is not None
    assert encontrado.id == producto_a.id


def test_menor_diferencia_gana_sobre_producto_creado_antes(db_session):
    from app.services.stock import buscar_producto_coincidente

    # El primero en crearse (id menor) queda más lejos; el segundo debe ganar por menor diferencia.
    _crear_producto(db_session, largo_mm=1200.9, ancho_mm=600.9)
    producto_mas_cercano = _crear_producto(db_session, largo_mm=1200.1, ancho_mm=600.1)

    encontrado = buscar_producto_coincidente(
        db_session,
        material="SAE_1010",
        espesor_mm=2.1,
        largo_mm=1200.0,
        ancho_mm=600.0,
        margen_tolerancia_mm=1.0,
    )
    assert encontrado is not None
    assert encontrado.id == producto_mas_cercano.id
