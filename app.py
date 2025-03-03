from flask import Flask, render_template, request, redirect, url_for, flash
from math import ceil
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import send_file
from decimal import Decimal
import mysql.connector

app = Flask(__name__)
app.secret_key = '123456'

# Configurações do banco de dados
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'orcamentos'
}

# Função para recuperar os valores fixos mais recentes
def get_valores_fixos():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM valores_fixos ORDER BY data_atualizacao DESC LIMIT 1')
    valores = cursor.fetchone()
    cursor.close()
    conn.close()
    return valores

# Rota para a página inicial (index)
@app.route('/', methods=['GET', 'POST'])
def index():
    valores_fixos = get_valores_fixos()

    if request.method == 'POST':
        descricao = request.form['descricao']
        distancia = request.form['distancia']  # Mantém como string

        # Verificar se os valores fixos estão configurados
        if not valores_fixos:
            flash('Valores fixos não configurados! Configure os valores fixos antes de criar um orçamento.', 'danger')
            return redirect(url_for('index'))

        # Converter Decimal para float (para cálculo)
        custo_combustivel = float(valores_fixos['custo_combustivel'])
        preco_insumos = float(valores_fixos['preco_insumos'])

        # Converter distância para float (já está com ponto)
        distancia_float = float(distancia)

        # Cálculo do total
        total = (custo_combustivel * distancia_float) + preco_insumos

        # Verificar se o total está dentro do intervalo permitido
        if total > 9999999999999.99:  # Ajuste conforme o tamanho da coluna
            flash('O valor total está fora do intervalo permitido!', 'danger')
            return redirect(url_for('index'))

        # Salvar no banco de dados (distância como string)
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orcamentos (descricao, custo_combustivel, distancia, preco_insumos, total)
            VALUES (%s, %s, %s, %s, %s)
        ''', (descricao, custo_combustivel, distancia, preco_insumos, total))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Orçamento salvo com sucesso!', 'success')
        return redirect(url_for('historico'))

    return render_template('index.html', valores_fixos=valores_fixos)

# Rota para salvar valores fixos
@app.route('/salvar_valores_fixos', methods=['POST'])
def salvar_valores_fixos():
    custo_combustivel = float(request.form['custo_combustivel'])
    preco_insumos = float(request.form['preco_insumos'])

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO valores_fixos (custo_combustivel, preco_insumos)
        VALUES (%s, %s)
    ''', (custo_combustivel, preco_insumos))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Valores fixos salvos com sucesso!', 'success')
    return redirect(url_for('index'))

# Rota para o histórico de orçamentos
@app.route('/historico')
def historico():
    # Parâmetros de paginação
    page = request.args.get('page', 1, type=int)  # Página atual (padrão: 1)
    per_page = 10  # Itens por página

    # Parâmetros de filtro
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    min_total = request.args.get('min_total')
    max_total = request.args.get('max_total')
    descricao = request.args.get('descricao')

    # Construir a consulta SQL
    query = 'SELECT * FROM orcamentos WHERE 1=1'
    params = []

    if data_inicio:
        query += ' AND data >= %s'
        params.append(data_inicio)
    if data_fim:
        query += ' AND data <= %s'
        params.append(data_fim)
    if min_total:
        query += ' AND total >= %s'
        params.append(float(min_total))
    if max_total:
        query += ' AND total <= %s'
        params.append(float(max_total))
    if descricao:
        query += ' AND descricao LIKE %s'
        params.append(f'%{descricao}%')

    # Contar o total de orçamentos (para paginação)
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f'SELECT COUNT(*) as total FROM ({query}) as subquery', tuple(params))
    total_orcamentos = cursor.fetchone()['total']
    cursor.close()

    # Calcular o número total de páginas
    total_pages = ceil(total_orcamentos / per_page)

    # Selecionar os orçamentos da página atual
    offset = (page - 1) * per_page
    query += ' ORDER BY data DESC LIMIT %s OFFSET %s'
    params.extend([per_page, offset])

    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, tuple(params))
    orcamentos = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('historico.html', orcamentos=orcamentos, page=page, total_pages=total_pages)

# Rota para realizar o download em pdf do orcamento
@app.route('/download_orcamento/<int:id>')
def download_orcamento(id):
    # Busque o orçamento no banco de dados
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM orcamentos WHERE id = %s', (id,))
    orcamento = cursor.fetchone()
    cursor.close()
    conn.close()

    # Crie o PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 730, f"Orçamento - {orcamento['descricao']}")
    p.drawString(100, 710, f"Custo Combustível: R$ {orcamento['custo_combustivel']:.2f}")
    p.drawString(100, 690, f"Distância: {orcamento['distancia']} km")
    p.drawString(100, 670, f"Preço Insumos: R$ {orcamento['preco_insumos']:.2f}")
    p.drawString(100, 650, f"Data: {orcamento['data']}")
    p.drawString(100, 630, f"Total: R$ {orcamento['total']:.2f}")
    p.showPage()
    p.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"orcamento_{orcamento['descricao']}.pdf", mimetype='application/pdf')

# Rota para editar orcamentos 
@app.route('/editar_orcamento/<int:id>', methods=['GET', 'POST'])
def editar_orcamento(id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        descricao = request.form['descricao']
        custo_combustivel = float(request.form['custo_combustivel'])
        distancia = float(request.form['distancia'])
        preco_insumos = float(request.form['preco_insumos'])
        total = (custo_combustivel * distancia) + preco_insumos

        cursor.execute('''
            UPDATE orcamentos
            SET descricao = %s, custo_combustivel = %s, distancia = %s, preco_insumos = %s, total = %s
            WHERE id = %s
        ''', (descricao, custo_combustivel, distancia, preco_insumos, total, id))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Orçamento atualizado com sucesso!', 'success')
        return redirect(url_for('historico'))

    cursor.execute('SELECT * FROM orcamentos WHERE id = %s', (id,))
    orcamento = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('editar_orcamento.html', orcamento=orcamento)

# Rota para excluir orcamentos 
@app.route('/excluir_orcamento/<int:id>')
def excluir_orcamento(id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM orcamentos WHERE id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Orçamento excluído com sucesso!', 'success')  # Mensagem de sucesso
    return redirect(url_for('historico'))

if __name__ == '__main__':
    app.run(debug=True)