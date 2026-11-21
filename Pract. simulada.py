#Prof4
#Fase 4 - componente práctico - prácticas simuladas

import logging
import os
import re
from abc import ABC, abstractmethod
from enum import Enum


# 1. EXCEPCIONES PERSONALIZADAS
class ErrorSoftwareFJ(Exception):
    """Excepción base del sistema."""

class DatosInvalidosError(ErrorSoftwareFJ):
    """Un dato tiene un formato o valor incorrecto."""

class ParametroFaltanteError(ErrorSoftwareFJ):
    """Falta un parámetro obligatorio."""

class OperacionNoPermitidaError(ErrorSoftwareFJ):
    """La operación no es valida para el estado actual del objeto."""

class ServicioNoDisponibleError(ErrorSoftwareFJ):
    """El servicio solicitado no está disponible."""

class ReservaInvalidaError(ErrorSoftwareFJ):
    """No fue posible crear o procesar la reserva."""

class CalculoInconsistenteError(ErrorSoftwareFJ):
    """El cálculo de costos produjo un resultado inválido."""

# 2. ARCHIVO DE LOGS
RUTA_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "software_fj.log")

def obtener_logger():
    logger = logging.getLogger("software_fj")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    try:
        os.makedirs(os.path.dirname(RUTA_LOG), exist_ok=True)
        manejador = logging.FileHandler(RUTA_LOG, encoding="utf-8")
    except OSError:
        manejador = logging.StreamHandler()

    formato = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")
    manejador.setFormatter(formato)
    logger.addHandler(manejador)
    logger.propagate = False
    return logger


logger = obtener_logger()


# 3. VALIDACIONES REUTILIZABLES
def texto_requerido(valor, campo, minimo=2, maximo=80):
    if valor is None:
        raise ParametroFaltanteError(f"El campo '{campo}' es obligatorio.")
    if not isinstance(valor, str):
        raise DatosInvalidosError(f"El campo '{campo}' debe ser texto.")
    valor = valor.strip()
    if not valor:
        raise ParametroFaltanteError(f"El campo '{campo}' no puede estar vacío.")
    if not (minimo <= len(valor) <= maximo):
        raise DatosInvalidosError(
            f"El campo '{campo}' debe tener entre {minimo} y {maximo} caracteres."
        )
    return valor


def numero_positivo(valor, campo):
    if valor is None:
        raise ParametroFaltanteError(f"El campo '{campo}' es obligatorio.")
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise DatosInvalidosError(f"El campo '{campo}' debe ser numérico.")
    if valor != valor or valor in (float("inf"), float("-inf")):
        raise DatosInvalidosError(f"El campo '{campo}' no es un número válido.")
    if valor <= 0:
        raise DatosInvalidosError(f"El campo '{campo}' debe ser mayor que cero.")
    return valor


def entero_positivo(valor, campo):
    if valor is None:
        raise ParametroFaltanteError(f"El campo '{campo}' es obligatorio.")
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise DatosInvalidosError(f"El campo '{campo}' debe ser un número entero.")
    if valor <= 0:
        raise DatosInvalidosError(f"El campo '{campo}' debe ser mayor que cero.")
    return valor



# 4. CLASE ABSTRACTA BASE: ENTIDAD
class Entidad(ABC):

    _contadores = {}

    def __init__(self, prefijo):
        numero = Entidad._contadores.get(prefijo, 0) + 1
        Entidad._contadores[prefijo] = numero
        self._id = f"{prefijo}-{numero:04d}"

    @property
    def id(self):
        return self._id

    @abstractmethod
    def describir(self):
        """Cada clase hija debe explicar cómo se describe."""

    def __str__(self):
        return self.describir()


# 5. CLASE CLIENTE (encapsulación + validaciones)

_PATRON_CORREO = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
_PATRON_DOCUMENTO = re.compile(r"^\d{6,12}$")
_PATRON_TELEFONO = re.compile(r"^3\d{9}$")  # celular colombiano de 10 dígitos


class Cliente(Entidad):

    def __init__(self, nombre, documento, correo, telefono):
        self.nombre = nombre
        self.documento = documento
        self.correo = correo
        self.telefono = telefono
        super().__init__("CLI")

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        valor = texto_requerido(valor, "nombre", minimo=3, maximo=60)
        if not all(c.isalpha() or c.isspace() for c in valor):
            raise DatosInvalidosError("El nombre solo puede contener letras y espacios.")
        self._nombre = valor.title()

    @property
    def documento(self):
        return self._documento

    @documento.setter
    def documento(self, valor):
        if valor is None:
            raise ParametroFaltanteError("El campo 'documento' es obligatorio.")
        valor = str(valor).strip()
        if not _PATRON_DOCUMENTO.match(valor):
            raise DatosInvalidosError("El documento debe tener entre 6 y 12 dígitos.")
        self._documento = valor

    @property
    def correo(self):
        return self._correo

    @correo.setter
    def correo(self, valor):
        valor = texto_requerido(valor, "correo", minimo=6, maximo=80)
        if not _PATRON_CORREO.match(valor):
            raise DatosInvalidosError(f"El correo '{valor}' no tiene un formato válido.")
        self._correo = valor.lower()

    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, valor):
        if valor is None:
            raise ParametroFaltanteError("El campo 'teléfono' es obligatorio.")
        valor = str(valor).strip()
        if not _PATRON_TELEFONO.match(valor):
            raise DatosInvalidosError("El teléfono debe ser un celular de 10 dígitos (inicia en 3).")
        self._telefono = valor

    def describir(self):
        oculto = "*" * (len(self._documento) - 3) + self._documento[-3:]
        return f"[{self.id}] {self._nombre} | Doc: {oculto} | {self._correo} | Tel: {self._telefono}"


# 6. SERVICIOS: clase abstracta + 3 servicios especializados
class Servicio(Entidad, ABC):
    IVA = 0.19

    def __init__(self, nombre, tarifa_hora, disponible=True):
        self._nombre = texto_requerido(nombre, "nombre del servicio", minimo=3, maximo=60)
        self._tarifa_hora = numero_positivo(tarifa_hora, "tarifa por hora")
        if not isinstance(disponible, bool):
            raise DatosInvalidosError("'disponible' debe ser verdadero o falso.")
        self._disponible = disponible
        super().__init__("SER")

    @property
    def nombre(self):
        return self._nombre

    @property
    def tarifa_hora(self):
        return self._tarifa_hora

    @property
    def disponible(self):
        return self._disponible

    @disponible.setter
    def disponible(self, valor):
        if not isinstance(valor, bool):
            raise DatosInvalidosError("'disponible' debe ser verdadero o falso.")
        self._disponible = valor

    @abstractmethod
    def calcular_costo_base(self, horas):
        """Costo sin impuestos ni descuentos."""

    @abstractmethod
    def validar_parametros(self, horas):
        """Valida la duración y reglas propias del servicio."""

    @abstractmethod
    def describir(self):
        """Descripción del servicio."""

    @staticmethod
    def _validar_horas(horas, maximo):
        if horas is None:
            raise ParametroFaltanteError("La duración (horas) es obligatoria.")
        if isinstance(horas, bool) or not isinstance(horas, (int, float)):
            raise DatosInvalidosError("La duración debe ser un número.")
        if horas <= 0:
            raise DatosInvalidosError("La duración debe ser mayor que cero.")
        if horas > maximo:
            raise DatosInvalidosError(f"La duración máxima para este servicio es {maximo} horas.")

    def calcular_costo(self, horas, impuesto=0.0, descuento=0.0):
        self.validar_parametros(horas)
        if isinstance(impuesto, bool) or not isinstance(impuesto, (int, float)) or not 0 <= impuesto <= 1:
            raise DatosInvalidosError("El impuesto debe ser un valor entre 0 y 1.")
        if isinstance(descuento, bool) or not isinstance(descuento, (int, float)) or not 0 <= descuento < 1:
            raise DatosInvalidosError("El descuento debe ser un valor entre 0 y 1 (sin incluir 1).")

        base = self.calcular_costo_base(horas)
        total = base * (1 - descuento) * (1 + impuesto)
        if total <= 0:
            raise CalculoInconsistenteError(f"El costo calculado ({total}) no es válido.")
        return round(total, 2)

    def calcular_costo_con_iva(self, horas):
        return self.calcular_costo(horas, impuesto=self.IVA)

    def calcular_costo_con_descuento(self, horas, descuento):
        return self.calcular_costo(horas, descuento=descuento)


class ReservaSala(Servicio):
    RECARGO_PROYECTOR = 20000  # por hora
    MAX_HORAS = 8

    def __init__(self, nombre, tarifa_hora, capacidad, tiene_proyector=False, disponible=True):
        self._capacidad = entero_positivo(capacidad, "capacidad")
        if self._capacidad > 200:
            raise DatosInvalidosError("La capacidad máxima de una sala es 200 personas.")
        if not isinstance(tiene_proyector, bool):
            raise DatosInvalidosError("'tiene_proyector' debe ser verdadero o falso.")
        self._tiene_proyector = tiene_proyector
        super().__init__(nombre, tarifa_hora, disponible)

    def validar_parametros(self, horas):
        self._validar_horas(horas, self.MAX_HORAS)

    def calcular_costo_base(self, horas):
        extra = self.RECARGO_PROYECTOR if self._tiene_proyector else 0
        return (self._tarifa_hora + extra) * horas

    def describir(self):
        proy = "con proyector" if self._tiene_proyector else "sin proyector"
        estado = "disponible" if self._disponible else "no disponible"
        return (f"[{self.id}] Sala '{self._nombre}' | capacidad {self._capacidad} | {proy} | "
                f"${self._tarifa_hora:,.0f}/h | {estado}")


class AlquilerEquipo(Servicio):
    SEGURO_FIJO = 10000
    MAX_HORAS = 72

    def __init__(self, nombre, tarifa_hora, tipo_equipo, disponible=True):
        self._tipo_equipo = texto_requerido(tipo_equipo, "tipo de equipo", minimo=3, maximo=40)
        super().__init__(nombre, tarifa_hora, disponible)

    def validar_parametros(self, horas):
        self._validar_horas(horas, self.MAX_HORAS)

    def calcular_costo_base(self, horas):
        return self._tarifa_hora * horas + self.SEGURO_FIJO

    def describir(self):
        estado = "disponible" if self._disponible else "no disponible"
        return (f"[{self.id}] Alquiler '{self._nombre}' ({self._tipo_equipo}) | "
                f"${self._tarifa_hora:,.0f}/h + seguro ${self.SEGURO_FIJO:,} | {estado}")


class AsesoriaEspecializada(Servicio):
    MULTIPLICADORES = {"junior": 1.0, "senior": 1.5, "experto": 2.0}
    MAX_HORAS = 6

    def __init__(self, nombre, tarifa_hora, especialidad, nivel="junior", disponible=True):
        self._especialidad = texto_requerido(especialidad, "especialidad", minimo=3, maximo=50)
        nivel = texto_requerido(nivel, "nivel", minimo=3, maximo=10).lower()
        if nivel not in self.MULTIPLICADORES:
            raise DatosInvalidosError(
                f"Nivel '{nivel}' no válido. Opciones: {', '.join(self.MULTIPLICADORES)}."
            )
        self._nivel = nivel
        super().__init__(nombre, tarifa_hora, disponible)

    def validar_parametros(self, horas):
        self._validar_horas(horas, self.MAX_HORAS)

    def calcular_costo_base(self, horas):
        return self._tarifa_hora * self.MULTIPLICADORES[self._nivel] * horas

    def describir(self):
        estado = "disponible" if self._disponible else "no disponible"
        return (f"[{self.id}] Asesoría '{self._nombre}' en {self._especialidad} | nivel {self._nivel} | "
                f"${self._tarifa_hora:,.0f}/h | {estado}")


# 7. CLASE RESERVA
class EstadoReserva(Enum):
    PENDIENTE = "Pendiente"
    CONFIRMADA = "Confirmada"
    CANCELADA = "Cancelada"


class Reserva(Entidad):
    def __init__(self, cliente, servicio, horas):
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva requiere un cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva requiere un servicio válido.")
        if not servicio.disponible:
            raise ServicioNoDisponibleError(f"El servicio '{servicio.nombre}' no está disponible.")
        servicio.validar_parametros(horas)

        self._cliente = cliente
        self._servicio = servicio
        self._horas = horas
        self._estado = EstadoReserva.PENDIENTE
        self._costo_total = None
        super().__init__("RES")

    @property
    def cliente(self):
        return self._cliente

    @property
    def servicio(self):
        return self._servicio

    @property
    def horas(self):
        return self._horas

    @property
    def estado(self):
        return self._estado

    @property
    def costo_total(self):
        return self._costo_total

    def confirmar(self):
        if self._estado != EstadoReserva.PENDIENTE:
            raise OperacionNoPermitidaError(
                f"No se puede confirmar la reserva {self.id}: estado actual {self._estado.value}."
            )
        self._estado = EstadoReserva.CONFIRMADA
        logger.info("Reserva %s confirmada.", self.id)

    def cancelar(self):
        if self._estado == EstadoReserva.CANCELADA:
            raise OperacionNoPermitidaError(f"La reserva {self.id} ya estaba cancelada.")
        self._estado = EstadoReserva.CANCELADA
        logger.info("Reserva %s cancelada.", self.id)

    def procesar(self, impuesto=0.0, descuento=0.0):
        """try/except/else/finally con encadenamiento de excepciones."""
        try:
            costo = self._servicio.calcular_costo(self._horas, impuesto, descuento)
        except ErrorSoftwareFJ as error:
            raise ReservaInvalidaError(
                f"No se pudo procesar la reserva {self.id}: {error}"
            ) from error
        except Exception as error:
            raise CalculoInconsistenteError(
                f"Falla inesperada procesando la reserva {self.id}."
            ) from error
        else:
            self.confirmar()
            self._costo_total = costo
            return costo
        finally:
            logger.debug("Intento de procesamiento finalizado para %s.", self.id)

    def describir(self):
        costo = f"${self._costo_total:,.2f}" if self._costo_total is not None else "sin calcular"
        return (f"[{self.id}] {self._cliente.nombre} -> {self._servicio.nombre} | "
                f"{self._horas} h | {self._estado.value} | costo: {costo}")


# 8. GESTOR: listas internas + ejecución protegida

class GestorFJ:
    def __init__(self):
        self._clientes = []
        self._servicios = []
        self._reservas = []
        self.ultimo_error = None  

    @property
    def clientes(self):
        return list(self._clientes)

    @property
    def servicios(self):
        return list(self._servicios)

    @property
    def reservas(self):
        return list(self._reservas)

    def _ejecutar(self, descripcion, funcion):
        """Ejecuta una operación; si falla, registra el error y el programa sigue."""
        self.ultimo_error = None
        try:
            resultado = funcion()
        except ErrorSoftwareFJ as error:
            self.ultimo_error = str(error)
            logger.error("%s | %s: %s", descripcion, type(error).__name__, error)
            if error.__cause__ is not None:
                logger.error("   causa original -> %s: %s", type(error.__cause__).__name__, error.__cause__)
            print(f"   [ERROR CONTROLADO] {type(error).__name__}: {error}")
            return None
        except Exception as error:
            self.ultimo_error = f"Error inesperado: {error}"
            logger.critical("%s | Error inesperado %s: %s", descripcion, type(error).__name__, error)
            print(f"   [ERROR INESPERADO CONTROLADO] {type(error).__name__}: {error}")
            return None
        else:
            logger.info("%s | OK", descripcion)
            return resultado
        finally:
            logger.debug("Fin de operación: %s", descripcion)

    def registrar_cliente(self, **datos):
        def accion():
            cliente = Cliente(**datos)
            if any(c.documento == cliente.documento for c in self._clientes):
                raise DatosInvalidosError(f"Ya existe un cliente con el documento {cliente.documento}.")
            self._clientes.append(cliente)
            return cliente
        return self._ejecutar("Registrar cliente", accion)

    def agregar_servicio(self, clase_servicio, **datos):
        def accion():
            servicio = clase_servicio(**datos)
            self._servicios.append(servicio)
            return servicio
        return self._ejecutar(f"Crear servicio {getattr(clase_servicio, '__name__', clase_servicio)}", accion)

    def crear_reserva(self, cliente, servicio, horas):
        def accion():
            reserva = Reserva(cliente, servicio, horas)
            self._reservas.append(reserva)
            return reserva
        return self._ejecutar("Crear reserva", accion)

    def procesar_reserva(self, reserva, impuesto=0.0, descuento=0.0):
        return self._ejecutar(
            f"Procesar reserva {getattr(reserva, 'id', '?')}",
            lambda: reserva.procesar(impuesto, descuento),
        )

    def cancelar_reserva(self, reserva):
        return self._ejecutar(
            f"Cancelar reserva {getattr(reserva, 'id', '?')}",
            lambda: reserva.cancelar() or True,
        )


# 9. SIMULACIÓN: 12 operaciones válidas e inválidas
def titulo(n, texto):
    print(f"\n--- Operación {n}: {texto}")


def main():
    logger.info("===== INICIO DE LA SIMULACIÓN =====")
    g = GestorFJ()

    titulo(1, "Registro válido de cliente (Laura)")
    laura = g.registrar_cliente(nombre="Laura Gómez", documento="1085123456",
                                correo="laura@correo.com", telefono="3101234567")
    print("  ", laura)

    titulo(2, "Registro válido de cliente (Carlos)")
    carlos = g.registrar_cliente(nombre="Carlos Ruiz", documento="98765432",
                                 correo="carlos.ruiz@mail.co", telefono="3209876543")
    print("  ", carlos)

    titulo(3, "Registro INVÁLIDO: correo mal formado")
    g.registrar_cliente(nombre="Pedro Pérez", documento="123456789",
                        correo="pedro-correo", telefono="3001112233")

    titulo(4, "Registro INVÁLIDO: parámetro faltante (sin teléfono)")
    g.registrar_cliente(nombre="Ana Torres", documento="55443322",
                        correo="ana@mail.com", telefono=None)

    titulo(5, "Servicio válido: sala con proyector")
    sala = g.agregar_servicio(ReservaSala, nombre="Sala Innovación", tarifa_hora=50000,
                              capacidad=12, tiene_proyector=True)
    print("  ", sala)

    titulo(6, "Servicio válido: alquiler de portátil + asesoría")
    equipo = g.agregar_servicio(AlquilerEquipo, nombre="Portátil Pro", tarifa_hora=8000,
                                tipo_equipo="Portátil")
    asesoria = g.agregar_servicio(AsesoriaEspecializada, nombre="Arquitectura de Software",
                                  tarifa_hora=90000, especialidad="Software", nivel="experto")
    print("  ", equipo)
    print("  ", asesoria)

    titulo(7, "Servicio INVÁLIDO: tarifa negativa y nivel inexistente")
    g.agregar_servicio(ReservaSala, nombre="Sala Fantasma", tarifa_hora=-100, capacidad=5)
    g.agregar_servicio(AsesoriaEspecializada, nombre="Asesoría X", tarifa_hora=70000,
                       especialidad="Redes", nivel="dios")

    titulo(8, "Reserva exitosa + procesamiento con IVA y descuento")
    r1 = g.crear_reserva(laura, sala, 3)
    if r1:
        costo = g.procesar_reserva(r1, impuesto=0.19, descuento=0.10)
        print("  ", r1, "| costo calculado:", costo)

    titulo(9, "Reserva FALLIDA: duración excede el máximo (sala 20 h)")
    g.crear_reserva(carlos, sala, 20)

    titulo(10, "Reserva FALLIDA: servicio no disponible")
    equipo.disponible = False
    g.crear_reserva(carlos, equipo, 5)
    equipo.disponible = True  # se vuelve a habilitar

    titulo(11, "Operación no permitida: confirmar de nuevo / cancelar dos veces")
    r2 = g.crear_reserva(carlos, asesoria, 2)
    if r2:
        g.procesar_reserva(r2, impuesto=0.19)
        g.procesar_reserva(r2)   
        g.cancelar_reserva(r2)
        g.cancelar_reserva(r2)   

    titulo(12, "Reserva FALLIDA: cliente inválido (None) y descuento inválido")
    g.crear_reserva(None, sala, 2)
    r3 = g.crear_reserva(laura, equipo, 10)
    if r3:
        g.procesar_reserva(r3, descuento=1.5)

    print("\n===== RESUMEN =====")
    print(f"Clientes registrados: {len(g.clientes)}")
    print(f"Servicios creados:    {len(g.servicios)}")
    print(f"Reservas creadas:     {len(g.reservas)}")
    for r in g.reservas:
        print("  ", r)
    print(f"\nRevisa el archivo de logs en: {RUTA_LOG}")
    logger.info("===== FIN DE LA SIMULACIÓN =====")


# 10. INTERFAZ GRÁFICA (tkinter): aquí el usuario anota sus propios datos

import io
from contextlib import redirect_stdout

try:
    import tkinter as tk
    from tkinter import messagebox, scrolledtext, ttk
except ImportError:  
    tk = None


def a_numero(texto, campo, entero=False):
    """Convierte lo que se escribió en un formulario a número (con validación)."""
    texto = (texto or "").strip().replace(",", ".")
    if not texto:
        raise ParametroFaltanteError(f"El campo '{campo}' es obligatorio.")
    try:
        if entero:
            return int(texto)
        try:
            return int(texto)
        except ValueError:
            return float(texto)
    except ValueError as error:
        tipo = "un número entero" if entero else "un número"
        raise DatosInvalidosError(f"El campo '{campo}' debe ser {tipo}.") from error


class AplicacionFJ:
    TIPOS_SERVICIO = ["Sala de reuniones", "Alquiler de equipo", "Asesoría especializada"]

    def __init__(self, raiz):
        self.raiz = raiz
        self.gestor = GestorFJ()
        raiz.title("Software FJ - Clientes, Servicios y Reservas")
        raiz.geometry("980x680")

        self.pestanas = ttk.Notebook(raiz)
        self.pestanas.pack(fill="both", expand=True, padx=8, pady=8)

        self._crear_pestana_clientes()
        self._crear_pestana_servicios()
        self._crear_pestana_reservas()
        self._crear_pestana_simulacion()

        self.pestanas.bind("<<NotebookTabChanged>>", lambda e: self._refrescar())
        logger.info("Ventana principal iniciada.")

    def _campo(self, padre, texto, fila, ancho=32):
        ttk.Label(padre, text=texto).grid(row=fila, column=0, sticky="w", padx=6, pady=4)
        entrada = ttk.Entry(padre, width=ancho)
        entrada.grid(row=fila, column=1, sticky="w", padx=6, pady=4)
        return entrada

    def _tabla(self, padre, columnas, titulos, anchos, altura=8):
        marco = ttk.Frame(padre)
        marco.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=altura)
        for col, tit, ancho in zip(columnas, titulos, anchos):
            tabla.heading(col, text=tit)
            tabla.column(col, width=ancho, anchor="w")
        barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=barra.set)
        tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        return tabla

    def _seleccionado(self, tabla, lista):
        seleccion = tabla.selection()
        if not seleccion:
            return None
        for objeto in lista:
            if objeto.id == seleccion[0]:
                return objeto
        return None

    def _error_gestor(self):
        messagebox.showerror("No se pudo completar", self.gestor.ultimo_error or "Error desconocido.")

    def _error_formulario(self, error):
        logger.error("Formulario | %s: %s", type(error).__name__, error)
        messagebox.showerror("Dato no válido", str(error))

    def _crear_pestana_clientes(self):
        marco = ttk.Frame(self.pestanas)
        self.pestanas.add(marco, text="1. Clientes")

        form = ttk.LabelFrame(marco, text="Registrar cliente")
        form.pack(fill="x", padx=10, pady=10)
        self.e_nombre = self._campo(form, "Nombre completo:", 0)
        self.e_documento = self._campo(form, "Documento (6 a 12 dígitos):", 1)
        self.e_correo = self._campo(form, "Correo electrónico:", 2)
        self.e_telefono = self._campo(form, "Celular (10 dígitos, inicia en 3):", 3)
        ttk.Button(form, text="Registrar cliente", command=self._registrar_cliente).grid(
            row=4, column=1, sticky="w", padx=6, pady=8)

        self.tabla_clientes = self._tabla(
            marco, ("id", "nombre", "documento", "correo", "telefono"),
            ("ID", "Nombre", "Documento", "Correo", "Celular"), (80, 200, 120, 240, 120))

    def _registrar_cliente(self):
        cliente = self.gestor.registrar_cliente(
            nombre=self.e_nombre.get(), documento=self.e_documento.get(),
            correo=self.e_correo.get(), telefono=self.e_telefono.get())
        if cliente is None:
            self._error_gestor()
            return
        for entrada in (self.e_nombre, self.e_documento, self.e_correo, self.e_telefono):
            entrada.delete(0, "end")
        messagebox.showinfo("Cliente registrado", f"Se registró a {cliente.nombre} ({cliente.id}).")
        self._refrescar()


    def _crear_pestana_servicios(self):
        marco = ttk.Frame(self.pestanas)
        self.pestanas.add(marco, text="2. Servicios")

        form = ttk.LabelFrame(marco, text="Crear servicio")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Tipo de servicio:").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.c_tipo = ttk.Combobox(form, values=self.TIPOS_SERVICIO, state="readonly", width=30)
        self.c_tipo.current(0)
        self.c_tipo.grid(row=0, column=1, sticky="w", padx=6, pady=4)
        self.c_tipo.bind("<<ComboboxSelected>>", lambda e: self._cambiar_tipo())

        self.e_snombre = self._campo(form, "Nombre del servicio:", 1)
        self.e_tarifa = self._campo(form, "Tarifa por hora ($):", 2)

        # Campos extra que cambian según el tipo de servicio
        self.extra_sala = ttk.Frame(form)
        self.e_capacidad = self._campo(self.extra_sala, "Capacidad (personas):", 0)
        self.v_proyector = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.extra_sala, text="Incluye proyector (+$20.000 por hora)",
                        variable=self.v_proyector).grid(row=1, column=1, sticky="w", padx=6)

        self.extra_equipo = ttk.Frame(form)
        self.e_tipo_equipo = self._campo(self.extra_equipo, "Tipo de equipo:", 0)

        self.extra_asesoria = ttk.Frame(form)
        self.e_especialidad = self._campo(self.extra_asesoria, "Especialidad:", 0)
        ttk.Label(self.extra_asesoria, text="Nivel:").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        self.c_nivel = ttk.Combobox(self.extra_asesoria, values=list(AsesoriaEspecializada.MULTIPLICADORES),
                                    state="readonly", width=30)
        self.c_nivel.current(0)
        self.c_nivel.grid(row=1, column=1, sticky="w", padx=6, pady=4)

        ttk.Button(form, text="Crear servicio", command=self._crear_servicio).grid(
            row=4, column=1, sticky="w", padx=6, pady=8)
        self._cambiar_tipo()

        self.tabla_servicios = self._tabla(
            marco, ("id", "tipo", "nombre", "tarifa", "estado"),
            ("ID", "Tipo", "Nombre", "Tarifa por hora", "Estado"), (80, 160, 260, 130, 120))
        ttk.Button(marco, text="Cambiar disponibilidad del servicio seleccionado",
                   command=self._cambiar_disponibilidad).pack(anchor="w", padx=10, pady=(0, 10))

    def _cambiar_tipo(self):
        for frame in (self.extra_sala, self.extra_equipo, self.extra_asesoria):
            frame.grid_remove()
        frame = (self.extra_sala, self.extra_equipo, self.extra_asesoria)[self.c_tipo.current()]
        frame.grid(row=3, column=0, columnspan=2, sticky="w")

    def _crear_servicio(self):
        tipo = self.c_tipo.current()
        try:
            nombre = self.e_snombre.get()
            tarifa = a_numero(self.e_tarifa.get(), "tarifa por hora")
            if tipo == 0:
                clase = ReservaSala
                datos = dict(nombre=nombre, tarifa_hora=tarifa,
                             capacidad=a_numero(self.e_capacidad.get(), "capacidad", entero=True),
                             tiene_proyector=self.v_proyector.get())
            elif tipo == 1:
                clase = AlquilerEquipo
                datos = dict(nombre=nombre, tarifa_hora=tarifa, tipo_equipo=self.e_tipo_equipo.get())
            else:
                clase = AsesoriaEspecializada
                datos = dict(nombre=nombre, tarifa_hora=tarifa,
                             especialidad=self.e_especialidad.get(), nivel=self.c_nivel.get())
        except ErrorSoftwareFJ as error:
            self._error_formulario(error)
            return

        servicio = self.gestor.agregar_servicio(clase, **datos)
        if servicio is None:
            self._error_gestor()
            return
        for entrada in (self.e_snombre, self.e_tarifa, self.e_capacidad,
                        self.e_tipo_equipo, self.e_especialidad):
            entrada.delete(0, "end")
        self.v_proyector.set(False)
        messagebox.showinfo("Servicio creado", f"Se creó '{servicio.nombre}' ({servicio.id}).")
        self._refrescar()

    def _cambiar_disponibilidad(self):
        servicio = self._seleccionado(self.tabla_servicios, self.gestor.servicios)
        if servicio is None:
            messagebox.showinfo("Selecciona un servicio", "Haz clic sobre un servicio de la tabla.")
            return
        servicio.disponible = not servicio.disponible
        logger.info("Servicio %s ahora %s.", servicio.id,
                    "disponible" if servicio.disponible else "no disponible")
        self._refrescar()


    def _crear_pestana_reservas(self):
        marco = ttk.Frame(self.pestanas)
        self.pestanas.add(marco, text="3. Reservas")

        form = ttk.LabelFrame(marco, text="Crear reserva")
        form.pack(fill="x", padx=10, pady=10)
        ttk.Label(form, text="Cliente:").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.c_cliente = ttk.Combobox(form, state="readonly", width=45)
        self.c_cliente.grid(row=0, column=1, sticky="w", padx=6, pady=4)
        ttk.Label(form, text="Servicio:").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        self.c_servicio = ttk.Combobox(form, state="readonly", width=45)
        self.c_servicio.grid(row=1, column=1, sticky="w", padx=6, pady=4)
        self.e_horas = self._campo(form, "Duración (horas):", 2, ancho=10)
        ttk.Button(form, text="Crear reserva", command=self._crear_reserva).grid(
            row=3, column=1, sticky="w", padx=6, pady=8)

        self.tabla_reservas = self._tabla(
            marco, ("id", "cliente", "servicio", "horas", "estado", "costo"),
            ("ID", "Cliente", "Servicio", "Horas", "Estado", "Costo total"),
            (80, 190, 240, 70, 110, 140))

        acciones = ttk.LabelFrame(marco, text="Acciones sobre la reserva seleccionada")
        acciones.pack(fill="x", padx=10, pady=(0, 10))
        self.v_iva = tk.BooleanVar(value=False)
        ttk.Checkbutton(acciones, text="Aplicar IVA (19 %)", variable=self.v_iva).grid(
            row=0, column=0, padx=6, pady=6)
        ttk.Label(acciones, text="Descuento (%):").grid(row=0, column=1, padx=6)
        self.e_descuento = ttk.Entry(acciones, width=6)
        self.e_descuento.insert(0, "0")
        self.e_descuento.grid(row=0, column=2, padx=6)
        ttk.Button(acciones, text="Procesar y confirmar", command=self._procesar_reserva).grid(
            row=0, column=3, padx=10)
        ttk.Button(acciones, text="Cancelar reserva", command=self._cancelar_reserva).grid(
            row=0, column=4, padx=6)

    def _crear_reserva(self):
        clientes, servicios = self.gestor.clientes, self.gestor.servicios
        i_cli, i_ser = self.c_cliente.current(), self.c_servicio.current()
        cliente = clientes[i_cli] if 0 <= i_cli < len(clientes) else None
        servicio = servicios[i_ser] if 0 <= i_ser < len(servicios) else None
        try:
            horas = a_numero(self.e_horas.get(), "duración (horas)")
        except ErrorSoftwareFJ as error:
            self._error_formulario(error)
            return

        reserva = self.gestor.crear_reserva(cliente, servicio, horas)
        if reserva is None:
            self._error_gestor()
            return
        self.e_horas.delete(0, "end")
        messagebox.showinfo("Reserva creada", f"Reserva {reserva.id} creada en estado Pendiente.\n"
                                              "Ahora selecciónala en la tabla y presiona 'Procesar y confirmar'.")
        self._refrescar()

    def _reserva_seleccionada(self):
        reserva = self._seleccionado(self.tabla_reservas, self.gestor.reservas)
        if reserva is None:
            messagebox.showinfo("Selecciona una reserva", "Haz clic sobre una reserva de la tabla.")
        return reserva

    def _procesar_reserva(self):
        reserva = self._reserva_seleccionada()
        if reserva is None:
            return
        try:
            texto = self.e_descuento.get().strip()
            descuento = (a_numero(texto, "descuento") / 100) if texto else 0.0
        except ErrorSoftwareFJ as error:
            self._error_formulario(error)
            return
        impuesto = Servicio.IVA if self.v_iva.get() else 0.0

        costo = self.gestor.procesar_reserva(reserva, impuesto, descuento)
        if costo is None:
            self._error_gestor()
        else:
            messagebox.showinfo("Reserva confirmada", f"Reserva {reserva.id} confirmada.\n"
                                                      f"Costo total: ${costo:,.2f}")
        self._refrescar()

    def _cancelar_reserva(self):
        reserva = self._reserva_seleccionada()
        if reserva is None:
            return
        if self.gestor.cancelar_reserva(reserva) is None:
            self._error_gestor()
        else:
            messagebox.showinfo("Reserva cancelada", f"La reserva {reserva.id} fue cancelada.")
        self._refrescar()


    def _crear_pestana_simulacion(self):
        marco = ttk.Frame(self.pestanas)
        self.pestanas.add(marco, text="4. Simulación y log")

        botones = ttk.Frame(marco)
        botones.pack(fill="x", padx=10, pady=10)
        ttk.Button(botones, text="Ejecutar las 12 operaciones de ejemplo",
                   command=self._ejecutar_simulacion).pack(side="left", padx=(0, 10))
        ttk.Button(botones, text="Ver archivo de logs", command=self._ver_log).pack(side="left")

        self.caja = scrolledtext.ScrolledText(marco, font=("Consolas", 10), wrap="word", state="disabled")
        self.caja.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _escribir(self, texto):
        self.caja.config(state="normal")
        self.caja.delete("1.0", "end")
        self.caja.insert("1.0", texto)
        self.caja.config(state="disabled")

    def _ejecutar_simulacion(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main()  
        self._escribir(buffer.getvalue())

    def _ver_log(self):
        try:
            with open(RUTA_LOG, encoding="utf-8") as archivo:
                self._escribir(archivo.read())
        except OSError as error:
            self._escribir(f"No se pudo leer el archivo de logs: {error}")


    def _refrescar(self):
        for tabla in (self.tabla_clientes, self.tabla_servicios, self.tabla_reservas):
            tabla.delete(*tabla.get_children())

        for c in self.gestor.clientes:
            oculto = "*" * (len(c.documento) - 3) + c.documento[-3:]
            self.tabla_clientes.insert("", "end", iid=c.id,
                                       values=(c.id, c.nombre, oculto, c.correo, c.telefono))
        for s in self.gestor.servicios:
            estado = "Disponible" if s.disponible else "No disponible"
            self.tabla_servicios.insert("", "end", iid=s.id,
                                        values=(s.id, type(s).__name__, s.nombre,
                                                f"${s.tarifa_hora:,.0f}", estado))
        for r in self.gestor.reservas:
            costo = f"${r.costo_total:,.2f}" if r.costo_total is not None else "-"
            self.tabla_reservas.insert("", "end", iid=r.id,
                                       values=(r.id, r.cliente.nombre, r.servicio.nombre,
                                               r.horas, r.estado.value, costo))

        self._llenar_combo(self.c_cliente, [f"{c.id} - {c.nombre}" for c in self.gestor.clientes])
        self._llenar_combo(self.c_servicio, [f"{s.id} - {s.nombre}" for s in self.gestor.servicios])

    @staticmethod
    def _llenar_combo(combo, valores):
        indice = combo.current()
        combo["values"] = valores
        if valores:
            combo.current(indice if 0 <= indice < len(valores) else 0)
        else:
            combo.set("")


if __name__ == "__main__":
    if tk is None:
        print("tkinter no está disponible: se ejecuta la simulación en consola.")
        main()
    else:
        try:
            raiz = tk.Tk()
        except tk.TclError:
            print("No hay pantalla gráfica disponible: se ejecuta la simulación en consola.")
            main()
        else:
            AplicacionFJ(raiz)
            raiz.mainloop()
