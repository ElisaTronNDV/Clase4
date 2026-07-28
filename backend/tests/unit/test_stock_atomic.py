import tempfile
import threading
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _nuevo_producto(**overrides):
    from app.models.producto import Producto

    datos = dict(
        material="SAE_1010",
        espesor_mm=2.1,
        largo_mm=1200.0,
        ancho_mm=600.0,
        stock_fisico=100.0,
        stock_comprometido=0.0,
        punto_pedido=5.0,
    )
    datos.update(overrides)
    return Producto(**datos)


def test_aplicar_delta_stock_acumula_deltas_secuenciales(db_session):
    from app.services.stock import aplicar_delta_stock

    producto = _nuevo_producto()
    db_session.add(producto)
    db_session.commit()

    aplicar_delta_stock(db_session, producto.id, "stock_comprometido", 3.0)
    db_session.commit()
    aplicar_delta_stock(db_session, producto.id, "stock_comprometido", 2.0)
    db_session.commit()

    db_session.refresh(producto)
    assert producto.stock_comprometido == 5.0
    assert producto.stock_fisico == 100.0


def test_aplicar_delta_stock_descuenta_stock_fisico(db_session):
    from app.services.stock import aplicar_delta_stock

    producto = _nuevo_producto(stock_fisico=50.0)
    db_session.add(producto)
    db_session.commit()

    aplicar_delta_stock(db_session, producto.id, "stock_fisico", -4.0)
    db_session.commit()

    db_session.refresh(producto)
    assert producto.stock_fisico == 46.0


def test_aplicar_delta_stock_no_pisa_commit_de_otra_sesion(db_session):
    """El delta MUST aplicarse como UPDATE col = col + :delta sobre el valor real de la
    fila (research.md §3), no como lectura-en-Python-más-escritura: si otra sesión ya
    commiteó un delta propio, el siguiente delta tiene que sumarse sobre ese resultado."""
    from app.services.stock import aplicar_delta_stock

    producto = _nuevo_producto()
    db_session.add(producto)
    db_session.commit()
    producto_id = producto.id

    OtraSession = sessionmaker(bind=db_session.get_bind())
    otra_sesion = OtraSession()
    aplicar_delta_stock(otra_sesion, producto_id, "stock_comprometido", 4.0)
    otra_sesion.commit()
    otra_sesion.close()

    aplicar_delta_stock(db_session, producto_id, "stock_comprometido", 3.0)
    db_session.commit()

    db_session.refresh(producto)
    assert producto.stock_comprometido == 7.0


def test_aplicar_delta_stock_concurrente_no_pierde_actualizaciones():
    from app.db.session import Base
    from app.services.stock import aplicar_delta_stock

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    ruta_db = Path(tmp.name)
    engine = create_engine(f"sqlite:///{ruta_db}", connect_args={"timeout": 30})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)

    setup = SessionLocal()
    producto = _nuevo_producto(stock_fisico=1000.0)
    setup.add(producto)
    setup.commit()
    producto_id = producto.id
    setup.close()

    n_hilos = 8
    incrementos_por_hilo = 15
    errores = []

    def trabajador():
        sesion = SessionLocal()
        try:
            for _ in range(incrementos_por_hilo):
                aplicar_delta_stock(sesion, producto_id, "stock_comprometido", 1.0)
                sesion.commit()
        except Exception as exc:  # pragma: no cover - se reporta en el assert final
            errores.append(exc)
        finally:
            sesion.close()

    hilos = [threading.Thread(target=trabajador) for _ in range(n_hilos)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()

    try:
        assert not errores, errores
        verificacion = SessionLocal()
        producto_final = verificacion.get(type(producto), producto_id)
        assert producto_final.stock_comprometido == n_hilos * incrementos_por_hilo
        verificacion.close()
    finally:
        engine.dispose()
        ruta_db.unlink(missing_ok=True)
