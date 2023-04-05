from tempfile import template
from MySQLdb.cursors import Cursor

from xml.sax.handler import feature_external_ges

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask.wrappers import Request
from flask_mysqldb import MySQL
from datetime import date, datetime, timedelta
import re

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'clinica'
mysql = MySQL(app)

app.secret_key = "mysecretkey"

# <--Redirección a las paginas-->


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/link_registro')
def p_register():
    datos = ['', '', '', '', '', '', '', '']
    return render_template('registrate.html', datos=datos)


@app.route('/link_login')
def p_login():
    return render_template('login.html')


@app.route('/psicologos')
def psico():
    return render_template('psico.html')


@app.route('/admin')
def admin():
    return render_template('login_admin.html')


@app.route('/loginadmin')
def loginadmin():
    return render_template('admin.html')


@app.route('/login_pisco')
def login_pisco():
    return render_template('login_pisco.html')


@app.route('/general')
def informacion():
    return render_template('general.html')


# <--Fin de la redirección(solo redireccionan)-->

# Formulario de registro
@app.route('/register', methods=['POST'])
def register():
    msg = ''
    if request.method == 'POST':
        nombres = request.form['txtnombre']
        apellidos = request.form['txtapellido']
        telefono = request.form['contact_phone']
        correo = request.form['txtusurio']
        nombre_u = request.form['txtnameuse']
        contraseña = request.form['txtpassword']
        estado = request.form['id_estado']
        hora = ['txtfecha']
        datos = [nombres, apellidos, telefono,
                 correo, nombre_u, contraseña, hora]

        # Comprobar si el email existe
        cursor = mysql.connection.cursor()
        cursor.execute(
            'SELECT * FROM usuario WHERE correo = %s', [str(correo)])
        emails = cursor.fetchone()
        cursor.close()
        if emails:
            msg = "Ya existe un usuario registrado con el correo indicado"
            return render_template('register.html', datos=datos, msg=msg)

        # guardar en la BD

        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO usuario (usuario, password, tipo, nombre, apellido, telefono, correo, id_estado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                       (nombre_u, contraseña, 3, nombres, apellidos, telefono, correo, estado))
        mysql.connection.commit()
        msg = 'Se ha creado la cuenta correctamente'
        return render_template('login.html', msg=msg)


@app.route('/login', methods=['POST'])
def login():
    msg = ''
    if request.method == 'POST':
        email = request.form['txtusurio']
        password = request.form['txtpassword']
        cursor = mysql.connection.cursor()
        cursor.execute(
            'SELECT * FROM usuario WHERE correo = %s AND password = %s', (email, password))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['id'] = user[0]
            session['usuario'] = user[1]
            session['tipo'] = user[3]
            session['nombre'] = user[4]
            session['apellido'] = user[5]
            session['telefono'] = user[6]
            session['correo'] = user[7]
            session['estado'] = user[8]
            return redirect(url_for('index'))
        else:
            # cuenta no existe
            msg = 'Usuario / Contraseña incorrecto!'
            return render_template('login.html', msg=msg)


# login admin
@app.route('/indexadmin', methods=['POST'])
def indexadmin():
    msg = ''
    if request.method == 'POST':
        emaila = request.form['usuario']
        passworda = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute(
            'SELECT * FROM usuario where correo = %s AND password = %s', (emaila, passworda))
        user = cursor.fetchone()
        if user:

            return redirect(url_for('loginadmin'))
        else:
            # cuenta no existe
            msg = 'Usuario / Contraseña incorrecto!'
            return render_template('login_admin.html', msg=msg)


# loginadmin
@app.route('/loginpsico')
def loginpsico():
    return render_template('index_psico.html')


# login psicologo
@app.route('/indexpsico', methods=['POST'])
def indexpsico():
    msg = ''
    if request.method == 'POST':
        emailp = request.form['usuariop']
        passwordp = request.form['passwordp']
        cursor = mysql.connection.cursor()
        cursor.execute(
            'SELECT * FROM psicologos WHERE correo = %s AND contraseña = %s', (emailp, passwordp))
        user = cursor.fetchone()
        if user:
            return redirect(url_for('loginpsico'))
        else:
            # cuenta no existe
            msg = 'Usuario / Contraseña incorrecto!'
            return render_template('login_pisco.html', msg=msg)


# Cerrar sesion
@app.route('/logout')
def logout():
    # removemos los datos de la sesión para cerrar sesión
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('usuario', None)
    session.pop('tipo', None)
    session.pop('nombre', None)
    session.pop('apellido', None)
    session.pop('telefono', None)
    session.pop('correo', None)
    session.pop('estado', None)
    # Redirige a la pagina de login
    return redirect(url_for('p_login'))


# Verificar estado de las citas, si ya hay espacio
def verificar_cita(fecha):
    cursor = mysql.connect.cursor()
    fecha_min = fecha - timedelta(minutes=60)
    fecha_max = fecha + timedelta(minutes=60)
    query = "SELECT * FROM cita WHERE fecha BETWEEN %s AND %s"
    cursor.execute(query, (fecha_min, fecha_max))
    result = cursor.fetchone()
    if result:
        return True
    else:
        return False


# Agendar cita
@app.route('/agendar_cita')
def agcita():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM psicologos')
    data1 = cur.fetchall()
    print(data1)
    cur.close()
    return render_template('ag_cita.html', detalles=data1)


@app.route('/guardar_detalles', methods=['POST'])
def guardar_detalles():
    msg = ''
    id_paciente = request.form['txtid']
    id_medico = request.form['id_doctor']
    fecha_str = request.form['txtfecha']
    fecha = datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M')
    duracion = 20
    if verificar_cita(fecha):
        msg = 'Lo siento, y hay una cita asignada a esa hora.'
    else:
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO cita(id_paciente, id_medico, fecha, estado_cita, horario) VALUES (%s, %s, %s, %s, %s)',
                       (id_paciente, id_medico, fecha, 'Aceptado', fecha))
        mysql.connection.commit()
        msg = 'La Cita se agendó correctamente.'
    return render_template('general.html', msg=msg)


@app.route('/detalles_admin', methods=['POST'])
def detalles_admin():
    msg = ''
    if request.method == 'POST':
        nombre = request.form['id_paciente']
        apellido = request.form['txtapellido']
        telefono = request.form['contact_phone']
        id_medico = request.form['id_doctor']
        fecha = request.form['txtfecha']
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO cita(id_paciente,id_medico, fecha, estado_cita, horario,nombre,apellido) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                       (nombre, id_medico, fecha, 'Aceptado', apellido))
        detalle = cursor.fecthone()
        mysql.connection.commit()
        msg = 'Se ha actualizado el reporte correctamente'
        return redirect(url_for('index', msg=msg), detalles=detalle)


@app.route('/citas')
def citas():
    cur = mysql.connection.cursor()
    cur.execute('SELECT c.id_cita, u.nombre, u.apellido, c.id_medico, fecha, estado_cita, observaciones FROM cita c, usuario u order by fecha asc ;')
    data = cur.fetchall()
    cur.close()
    return render_template('citas.html', reporte=data)


# ya
@app.route('/ad_cita')
def ad_cita():
    return render_template('ag_cita_admin.html')


# agregar cita psicologo
@app.route('/cita_psico')
def cita_psico():
    return render_template('ag_cita_psico.html')


@app.route('/medicos')
def medicos():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM psicologos order by id ASC  ;')
    data = cur.fetchall()
    cur.close()
    return render_template('medicos.html', reporte=data)


@app.route('/admin_abre')
def admin_abre():
    return render_template('admin.html')


if __name__ == '__main__':
    app.run(port=5000, debug=True)
