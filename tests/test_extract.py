from bot.lookup.extract import extract_result

SUCCESS_HTML = """
<html><body>
<div class="clConteudoEsquerda">
    <p>
        <span class="clConteudoDados">N<sup>o</sup> do CPF: <b>700.829.061-65</b></span>
        <span class="clConteudoDados">Nome: <b>JOSE CARLOS MIRANDA LEITE</b></span>
        <span class="clConteudoDados">Data de Nascimento: <b>02/08/1997</b></span>
        <span class="clConteudoDados">Situação Cadastral: <b>REGULAR</b></span>
        <span class="clConteudoDados">Data da Inscrição: <b>24/08/2010</b></span>
        <span class="clConteudoDados">Digito Verificador: <b>00</b></span>
    </p>
</div>
<div class="clConteudoEsquerda">
    <p>
        <span class="clConteudoComp">Comprovante emitido às: <b>14:32:23</b> do dia <b>20/09/2026</b> (hora e data de Brasília).</span>
        <span class="clConteudoComp">Código de controle do comprovante: <b>5CA9.B28F.E815.FCA5</b></span>
    </p>
</div>
</body></html>
"""

ERROR_HTML = """
<html><body>
<div id="idMensagemErro">
    <span class="mensagemForm">O Anti-Robô não foi preenchido corretamente. Por favor, envie novamente.</span>
</div>
</body></html>
"""

UNRECOGNIZED_HTML = "<html><body><p>something else</p></body></html>"


def test_extract_success_populates_record():
    result = extract_result(SUCCESS_HTML)

    assert result.success is True
    assert result.record is not None
    assert result.record.cpf == "700.829.061-65"
    assert result.record.name == "JOSE CARLOS MIRANDA LEITE"
    assert result.record.birth_date == "02/08/1997"
    assert result.record.status == "REGULAR"
    assert result.record.registration_date == "24/08/2010"
    assert result.record.check_digit == "00"
    assert result.record.control_code == "5CA9.B28F.E815.FCA5"
    assert "14:32:23" in result.record.issued_at


def test_extract_error_message():
    result = extract_result(ERROR_HTML)

    assert result.success is False
    assert result.record is None
    assert "Anti-Robô" in result.message


def test_extract_unrecognized_response():
    result = extract_result(UNRECOGNIZED_HTML)

    assert result.success is False
    assert result.record is None
    assert result.message == "unrecognized response"
