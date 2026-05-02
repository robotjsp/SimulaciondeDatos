import random
import collections
from typing import List, Dict, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# REGLAS Y CATEGORÍAS DE LOS DADOS
# ─────────────────────────────────────────────────────────────────────────────

CATEGORIAS = [
    'unos', 'doses', 'treses', 'cuatros', 'cincos', 'seises',
    'trio', 'poker', 'full_house', 'escalera_menor',
    'escalera_mayor', 'yahtzee', 'chance'
]

NOMBRE_CATEGORIA = {
    'unos': 'Unos', 'doses': 'Doses', 'treses': 'Treses',
    'cuatros': 'Cuatros', 'cincos': 'Cincos', 'seises': 'Seises',
    'trio': 'Trío', 'poker': 'Póker', 'full_house': 'Full House',
    'escalera_menor': 'Escalera Menor', 'escalera_mayor': 'Escalera Mayor',
    'yahtzee': 'Yahtzee', 'chance': 'Chance'
}

# ─────────────────────────────────────────────────────────────────────────────
# DISTRIBUCIÓN UNIFORME DISCRETA — NÚCLEO DEL MÉTODO MONTECARLO
# ─────────────────────────────────────────────────────────────────────────────

def lanzar_dado() -> int:
    """
    Genera un valor aleatorio con distribución uniforme discreta.
    """
    return random.randint(1, 6)


def lanzar_dados(dados: List[Dict]) -> List[Dict]:
    """
    Lanza los dados no bloqueados (simulación Monte Carlo).
    """
    for dado in dados:
        if not dado['bloqueado']:
            dado['valor'] = lanzar_dado()
    return dados


# ─────────────────────────────────────────────────────────────────────────────
# CÁLCULO DE PUNTUACIÓN
# ─────────────────────────────────────────────────────────────────────────────

def calcular_puntuacion(categoria: str, valores: List[int]) -> int:
    """
    Calcula la puntuación para una categoría dada.
    """
    conteos = collections.Counter(valores)
    frecuencias = list(conteos.values())
    suma_total = sum(valores)
    valores_unicos = sorted(conteos.keys())

    # ── Sección superior ────────────────────
    mapa_num = {'unos': 1, 'doses': 2, 'treses': 3,
                'cuatros': 4, 'cincos': 5, 'seises': 6}
    if categoria in mapa_num:
        num = mapa_num[categoria]
        return conteos.get(num, 0) * num

    # ── La Sección inferior ────────────────
    if categoria == 'trio':
        return suma_total if any(f >= 3 for f in frecuencias) else 0

    if categoria == 'poker':
        return suma_total if any(f >= 4 for f in frecuencias) else 0

    if categoria == 'full_house':
        return 25 if (3 in frecuencias and 2 in frecuencias) else 0

    if categoria == 'escalera_menor':
        patrones = [{1, 2, 3, 4}, {2, 3, 4, 5}, {3, 4, 5, 6}]
        return 30 if any(p.issubset(set(valores)) for p in patrones) else 0

    if categoria == 'escalera_mayor':
        return 40 if valores_unicos in [[1, 2, 3, 4, 5], [2, 3, 4, 5, 6]] else 0

    if categoria == 'yahtzee':
        return 50 if any(f == 5 for f in frecuencias) else 0

    if categoria == 'chance':
        return suma_total

    return 0


# ─────────────────────────────────────────────────────────────────────────────
# ESTRATEGIA AUTOMATIZADA PARA EL JUGADOR
# ─────────────────────────────────────────────────────────────────────────────

def elegir_dados_a_bloquear(dados: List[Dict], categorias_disponibles: List[str]) -> List[Dict]:
    """
    Teoria de greedy: bloqueamos los dados que maximizan la puntuación
    potencial en las categorías disponibles.

    """
    valores = [d['valor'] for d in dados]
    conteos = collections.Counter(valores)

    # Desbloquear todos primero
    for d in dados:
        d['bloqueado'] = False

    # 1. Yahtzee: si hay 4 o 5 iguales, conservar
    if 'yahtzee' in categorias_disponibles:
        max_rep = max(conteos.values())
        if max_rep >= 4:
            valor_objetivo = max(k for k, v in conteos.items() if v == max_rep)
            for d in dados:
                if d['valor'] == valor_objetivo:
                    d['bloqueado'] = True
            return dados

    # 2. Poker / Trío: si hay 3+ iguales, conservar
    for cat in ['poker', 'trio']:
        if cat in categorias_disponibles:
            umbral = 4 if cat == 'poker' else 3
            max_rep = max(conteos.values())
            if max_rep >= umbral:
                valor_objetivo = max(k for k, v in conteos.items() if v == max_rep)
                for d in dados:
                    if d['valor'] == valor_objetivo:
                        d['bloqueado'] = True
                return dados

    # 3. Full House: si hay 3+2
    if 'full_house' in categorias_disponibles:
        if sorted(conteos.values(), reverse=True)[:2] == [3, 2]:
            for d in dados:
                d['bloqueado'] = True
            return dados
        if 3 in conteos.values():
            v3 = [k for k, v in conteos.items() if v >= 3][0]
            for d in dados:
                if d['valor'] == v3:
                    d['bloqueado'] = True
            return dados

    # 4. Escalera: conservar dados consecutivos
    for cat, longitud in [('escalera_mayor', 5), ('escalera_menor', 4)]:
        if cat in categorias_disponibles:
            unicos = sorted(set(v['valor'] for v in dados))
            mejor_seq = []
            seq_actual = [unicos[0]]
            for x in unicos[1:]:
                if x == seq_actual[-1] + 1:
                    seq_actual.append(x)
                else:
                    if len(seq_actual) > len(mejor_seq):
                        mejor_seq = seq_actual
                    seq_actual = [x]
            if len(seq_actual) > len(mejor_seq):
                mejor_seq = seq_actual
            if len(mejor_seq) >= longitud - 1:
                bloqueados = set(mejor_seq[:longitud])
                usados = set()
                for d in dados:
                    if d['valor'] in bloqueados and d['valor'] not in usados:
                        d['bloqueado'] = True
                        usados.add(d['valor'])
                return dados

    # 5. Conservar el dado con mayor valor (optimizar chance/seises)
    max_val = max(d['valor'] for d in dados)
    for d in dados:
        if d['valor'] == max_val:
            d['bloqueado'] = True
            break

    return dados


def elegir_mejor_categoria(valores: List[int], categorias_disponibles: List[str]) -> str:
    """
    Selecciona la categoría disponible que da la mayor puntuación.
    Si hay empate, prioriza categorías de mayor valor fijo segun greedy.
    """
    prioridad_fija = ['yahtzee', 'escalera_mayor', 'escalera_menor',
                      'full_house', 'poker', 'trio']

    mejor_cat = None
    mejor_pts = -1

    for cat in categorias_disponibles:
        pts = calcular_puntuacion(cat, valores)
        if pts > mejor_pts:
            mejor_pts = pts
            mejor_cat = cat
        elif pts == mejor_pts and mejor_cat is not None:
            # Priorizar categorías fijas sobre sumas
            if cat in prioridad_fija and mejor_cat not in prioridad_fija:
                mejor_cat = cat

    # Si la mejor puntuación es 0, usar 'chance' o primera disponible
    if mejor_pts == 0:
        if 'chance' in categorias_disponibles:
            mejor_cat = 'chance'
        else:
            mejor_cat = categorias_disponibles[0]

    return mejor_cat


# ─────────────────────────────────────────────────────────────────────────────
# SIMULACIÓN DE UN TURNO
# ─────────────────────────────────────────────────────────────────────────────

def simular_turno(jugador: Dict, estadisticas: Dict) -> Tuple[str, int]:
    """
    Simula un turno completo (hasta 3 lanzamientos).
    """
    dados = [{'valor': 1, 'bloqueado': False} for _ in range(5)]
    categorias_disponibles = [c for c in CATEGORIAS
                               if c not in jugador['puntuaciones']]

    for lanzamiento in range(3):
        # Lanzar dados no bloqueados
        dados = lanzar_dados(dados)
        valores = [d['valor'] for d in dados]

        # Registrar estadísticas de lanzamiento
        estadisticas['total_lanzamientos'] += sum(1 for d in dados if not d['bloqueado'])
        estadisticas['suma_total'] += sum(d['valor'] for d in dados if not d['bloqueado'])
        for v in valores:
            estadisticas['frecuencia_caras'][v] += 1

        # En el último lanzamiento no se bloquea más
        if lanzamiento < 2:
            dados = elegir_dados_a_bloquear(dados, categorias_disponibles)

    # Elegir categoría y registrar puntuación
    valores_finales = [d['valor'] for d in dados]
    categoria = elegir_mejor_categoria(valores_finales, categorias_disponibles)
    puntos = calcular_puntuacion(categoria, valores_finales)

    jugador['puntuaciones'][categoria] = puntos
    jugador['total'] += puntos

    if categoria == 'yahtzee' and puntos == 50:
        estadisticas['yahtzees'] += 1

    return categoria, puntos


# ─────────────────────────────────────────────────────────────────────────────
# SIMULACIÓN DE UN JUEGO COMPLETO
# ─────────────────────────────────────────────────────────────────────────────

def simular_juego() -> Dict:
    """
    Simulamos un juego completo de Yahtzee con 2 jugadores con 13 turnos cada uno.
    """
    jugadores = [
        {'nombre': 'Jugador 1', 'puntuaciones': {}, 'total': 0},
        {'nombre': 'Jugador 2', 'puntuaciones': {}, 'total': 0}
    ]

    estadisticas = {
        'total_lanzamientos': 0,
        'suma_total': 0,
        'frecuencia_caras': collections.Counter(),
        'yahtzees': 0
    }

    historial_turnos = []

    # 13 rondas × 2 jugadores
    for ronda in range(13):
        for jugador in jugadores:
            cat, pts = simular_turno(jugador, estadisticas)
            historial_turnos.append({
                'ronda': ronda + 1,
                'jugador': jugador['nombre'],
                'categoria': NOMBRE_CATEGORIA[cat],
                'puntos': pts
            })

    # Determinar ganador
    ganador = max(jugadores, key=lambda j: j['total'])

    return {
        'jugadores': jugadores,
        'ganador': ganador,
        'estadisticas': estadisticas,
        'historial': historial_turnos
    }


# ─────────────────────────────────────────────────────────────────────────────
# SIMULACIÓN MONTE CARLO — MÚLTIPLES PARTIDAS
# ─────────────────────────────────────────────────────────────────────────────

def simulacion_montecarlo(n_juegos: int = 10_000) -> Dict:
    """
    EJECUCION DE 10.000 simulaciones completas del juego Yahtzee.
    Nota: Al aumentar N, los resultados convergen a las probabilidades teóricas.

    """
    victorias = collections.Counter()
    puntajes_j1 = []
    puntajes_j2 = []
    total_yahtzees = 0
    total_lanzamientos = 0
    suma_lanzamientos = 0
    frecuencia_caras_global = collections.Counter()
    conteo_combinaciones = collections.Counter()

    for _ in range(n_juegos):
        resultado = simular_juego()
        j1, j2 = resultado['jugadores']
        est = resultado['estadisticas']

        victorias[resultado['ganador']['nombre']] += 1
        puntajes_j1.append(j1['total'])
        puntajes_j2.append(j2['total'])
        total_yahtzees += est['yahtzees']
        total_lanzamientos += est['total_lanzamientos']
        suma_lanzamientos += est['suma_total']
        frecuencia_caras_global.update(est['frecuencia_caras'])

        # Registrar qué combinaciones logró cada jugador (puntaje > 0)
        for jug in resultado['jugadores']:
            for cat, pts in jug['puntuaciones'].items():
                if pts > 0 and cat not in ['unos','doses','treses',
                                            'cuatros','cincos','seises','chance']:
                    conteo_combinaciones[cat] += 1

    promedio_j1 = sum(puntajes_j1) / n_juegos
    promedio_j2 = sum(puntajes_j2) / n_juegos
    promedio_dado = suma_lanzamientos / total_lanzamientos if total_lanzamientos else 0

    return {
        'n_juegos': n_juegos,
        'victorias': victorias,
        'prob_victoria_j1': victorias['Jugador 1'] / n_juegos,
        'prob_victoria_j2': victorias['Jugador 2'] / n_juegos,
        'promedio_puntaje_j1': promedio_j1,
        'promedio_puntaje_j2': promedio_j2,
        'max_puntaje_j1': max(puntajes_j1),
        'max_puntaje_j2': max(puntajes_j2),
        'min_puntaje_j1': min(puntajes_j1),
        'min_puntaje_j2': min(puntajes_j2),
        'total_yahtzees': total_yahtzees,
        'prob_yahtzee_por_juego': total_yahtzees / n_juegos,
        'promedio_dado': promedio_dado,
        'frecuencia_caras': frecuencia_caras_global,
        'total_lanzamientos': total_lanzamientos,
        'conteo_combinaciones': conteo_combinaciones
    }


# ─────────────────────────────────────────────────────────────────────────────
# RESPUESTA A LAS PREGUNTAS DEL LABORATORIO
# ─────────────────────────────────────────────────────────────────────────────

def responder_interrogantes(res: Dict) -> None:
    """
    Imprime las respuestas usando los resultados de la simulación.
    """
    n = res['n_juegos']
    total_lanz = res['total_lanzamientos']

    separador = "=" * 70

    print(f"\n{separador}")
    print("  RESPUESTA DEL LABORATORIO")
    print(f"  (basada en {n:,} simulaciones Monte Carlo)")
    print(separador)

    # ── Interrogante 1 ────────────────────────────────────────────────────
    print("\n PREGUNTA 1")

    print("   ¿Cuál es la distribución de probabilidad del juego?")
    print("   Cada dado posee una distribución Uniforme Discreta:")
    print("   P(X = k) = 1/6  para k ∈ {1, 2, 3, 4, 5, 6}")
    print(f"\n   Parámetros teóricos:")
    print(f"     Valor esperado   E[X]   = 3.5000")
    print(f"     Varianza         Var(X) = 2.9167")
    print(f"     Desv. estándar   σ      = 1.7078")
    print(f"\n   Resultados simulados ({total_lanz:,} lanzamientos totales):")
    print(f"     Promedio observado      = {res['promedio_dado']:.4f}  (teórico: 3.5000)")

    total_caras = sum(res['frecuencia_caras'].values())
    print(f"\n   Frecuencia relativa por cara (convergencia a 1/6 ≈ 16.67%):")
    for cara in range(1, 7):
        freq = res['frecuencia_caras'][cara]
        porcentaje = freq / total_caras * 100
        barra = '█' * int(porcentaje / 0.5)
        print(f"     Cara {cara}: {freq:>9,} veces  ({porcentaje:.2f}%)  {barra}")

    # ── Interrogante 2 ────────────────────────────────────────────────────
    print(f"\n{separador}")
    print("\n PREGUNTA 2")

    print("   ¿Cuál es la probabilidad de obtener Yahtzee en un turno?")
    print("   Segun la teoria, la probabilidad en un lanzamiento de 5 dados es la siguiente:")
    print("   P(Yahtzee) = 6 × (1/6)⁵ = 6/7776 ≈ 0.0772%")
    p_montecarlo = res['prob_yahtzee_por_juego'] / 13 * 100
    print(f"\n   Probabilidad estimada por Monte Carlo por turno ≈ {p_montecarlo:.4f}%")
    print(f"   Total de Yahtzees obtenidos: {res['total_yahtzees']:,} en {n:,} juegos")
    print(f"   Promedio de Yahtzees por juego: {res['prob_yahtzee_por_juego']:.4f}")
    print("\n   Conclusión: Con hasta 3 lanzamientos y estrategia de bloqueo,")
    print("   la probabilidad aumenta significativamente respecto al teórico.")

    # ── Interrogante 3 ────────────────────────────────────────────────────
    print(f"\n{separador}")
    print("\n PREGUNTA 3")

    print("   ¿Cuál es la probabilidad de que gane cada jugador?")
    print("\n  Si cada jugador juega igual de manera simétrica seria la siguiente:")
    print(f"   P(gana Jugador 1) = {res['prob_victoria_j1']:.4f}  ({res['prob_victoria_j1']*100:.2f}%)")
    print(f"   P(gana Jugador 2) = {res['prob_victoria_j2']:.4f}  ({res['prob_victoria_j2']*100:.2f}%)")
    empates = n - res['victorias']['Jugador 1'] - res['victorias']['Jugador 2']
    print(f"   Empates           = {empates}  ({empates/n*100:.2f}%)")
    print("\n   Conclusión: Con estrategia idéntica, la probabilidad de victoria")
    print("   es aproximadamente 50% para cada jugador, aunque el asar siempre definira al ganador.")

    # ── Interrogante 4 ────────────────────────────────────────────────────
    print(f"\n{separador}")
    print("\n PREGUNTA 4")
    print("   ¿Cuál es la puntuación promedio, mínima y máxima por jugador?")
    print(f"   {'Métrica':<25} {'Jugador 1':>12} {'Jugador 2':>12}")
    print(f"   {'-'*49}")
    print(f"   {'Puntaje promedio':<25} {res['promedio_puntaje_j1']:>12.1f} {res['promedio_puntaje_j2']:>12.1f}")
    print(f"   {'Puntaje máximo':<25} {res['max_puntaje_j1']:>12} {res['max_puntaje_j2']:>12}")
    print(f"   {'Puntaje mínimo':<25} {res['min_puntaje_j1']:>12} {res['min_puntaje_j2']:>12}")

    # ── Interrogante 5 ────────────────────────────────────────────────────
    print(f"\n{separador}")
    print("\n PREGUNTA 5")

    print("   ¿Con qué frecuencia se obtiene cada combinación especial?")
    print("\n  La frecuencia de jugador por juego es la siguiente:")
    orden = ['trio', 'poker', 'full_house', 'escalera_menor',
             'escalera_mayor', 'yahtzee']
    print(f"\n   {'Combinación':<20} {'Ocurrencias':>12} {'Prob/turno':>12}")
    print(f"   {'-'*44}")
    # Cada juego tiene 13 turnos × 2 jugadores = 26 oportunidades por combinación
    oportunidades = n * 2
    for cat in orden:
        ocurr = res['conteo_combinaciones'].get(cat, 0)
        prob = ocurr / oportunidades * 100
        print(f"   {NOMBRE_CATEGORIA[cat]:<20} {ocurr:>12,} {prob:>11.2f}%")

    # ── Interrogante 6 ────────────────────────────────────────────────────
    print(f"\n{separador}")
    print("\n PREGUNTA 6")

    print("   ¿El valor promedio del dado converge al valor esperado teórico?")
    print(f"   E[X] teórico                  = 3.5000")
    print(f"   Promedio simulado             = {res['promedio_dado']:.4f}")
    print(f"   Error absoluto                = {abs(res['promedio_dado'] - 3.5):.4f}")
    error_rel = abs(res['promedio_dado'] - 3.5) / 3.5 * 100
    print(f"   Error relativo                = {error_rel:.4f}%")
    print(f"\n   Con {total_lanz:,} lanzamientos, la Ley de los Grandes Números")
    print(f"   garantiza convergencia. Error relativo < 1% confirma validez")
    print(f"   del generador de números pseudoaleatorios (distribución uniforme).")

    print(f"\n{separador}\n")


# ─────────────────────────────────────────────────────────────────────────────
# INFORME DE UN JUEGO COMPLETO
# ─────────────────────────────────────────────────────────────────────────────

def mostrar_juego_ejemplo() -> None:

    print("\n" + "=" * 70)
    print(" (simulación detallada de un juego)")
    print("=" * 70)

    resultado = simular_juego()
    j1, j2 = resultado['jugadores']

    # Tabla de puntuaciones
    print(f"\n{'Categoría':<22} {'Jugador 1':>12} {'Jugador 2':>12}")
    print("-" * 46)
    for cat in CATEGORIAS:
        p1 = j1['puntuaciones'].get(cat, 0)
        p2 = j2['puntuaciones'].get(cat, 0)
        print(f"  {NOMBRE_CATEGORIA[cat]:<20} {p1:>12} {p2:>12}")

    print("-" * 46)
    print(f"  {'TOTAL':<20} {j1['total']:>12} {j2['total']:>12}")

    ganador = resultado['ganador']
    print(f"\n  🏆 GANADOR: {ganador['nombre']} con {ganador['total']} puntos")

    est = resultado['estadisticas']
    print(f"\n  Lanzamientos totales: {est['total_lanzamientos']}")
    print(f"  Promedio por dado:    {est['suma_total']/est['total_lanzamientos']:.2f}")
    print(f"  Yahtzees obtenidos:   {est['yahtzees']}")


# ─────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA PYTHON
# ─────────────────────────────────────────────────────────────────────────────


if __name__ == '__main__':


    print("\n" + "=" * 70)
    print("  LAB SIMULACIÓN CON YAHTZEE — MÉTODO DE MONTECARLO")
    print("  Distribución: Uniforme Discreta P(X=k) = 1/6, k ∈ {1..6}")
    print("=" * 70)

    # 1. Mostrar un juego de ejemplo con detalle
    mostrar_juego_ejemplo()

    # 2. Ejecutar simulación Monte Carlo
    # Reducimos para pruebas rápidas para ver obsilaciones
    N_SIMULACIONES = 10_000
    print(f"\n\nEjecutando {N_SIMULACIONES:,} simulaciones Monte Carlo...")
    resultados = simulacion_montecarlo(N_SIMULACIONES)
    print("Simulación completada.")

    # 3. Responder interrogantes
    responder_interrogantes(resultados)
