import re

import pytest

CODIGO_NEST_RE = re.compile(r"^NEST-\d{6,}$")


@pytest.mark.parametrize(
    "id_fila,esperado",
    [
        (1, "NEST-000001"),
        (42, "NEST-000042"),
        (999, "NEST-000999"),
        (123456, "NEST-123456"),
    ],
)
def test_generar_codigo_nest_formato(id_fila, esperado):
    from app.services.ordenes import generar_codigo_nest

    assert generar_codigo_nest(id_fila) == esperado


def test_generar_codigo_nest_no_trunca_ids_de_mas_de_seis_digitos():
    from app.services.ordenes import generar_codigo_nest

    assert generar_codigo_nest(1234567) == "NEST-1234567"


def test_generar_codigo_nest_matchea_formato_general():
    from app.services.ordenes import generar_codigo_nest

    for id_fila in (1, 100, 999999):
        assert CODIGO_NEST_RE.match(generar_codigo_nest(id_fila))


def test_generar_codigo_nest_sin_colision_bajo_ids_sucesivos():
    from app.services.ordenes import generar_codigo_nest

    codigos = [generar_codigo_nest(id_fila) for id_fila in range(1, 1001)]
    assert len(set(codigos)) == 1000
