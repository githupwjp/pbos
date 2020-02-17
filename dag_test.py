from .dag import DAG


def test_dag():
    subword_score = {
        "l": 0.010088041794802646,
        "lo": 0.030347545000532588,
        "low": 0.04232451574608136,
        "o": 0.01302921039494376,
        "ow": 0.01930930643654368,
        "w": 0.0018104302068600111,
        "wost": 0.02335118654441226,
        "e": 0.02156951127304255,
        "es": 0.054121408112153484,
        "est": 0.0722032100772723,
        "s": 0.015434593934687147,
        "st": 0.044544566720156394,
        "t": 0.013228271492577652,
    }
    word = "lowest"
    dag = DAG(subword_score, word)

    assert dag.graph == [
        [0, 0.010088041794802646, 0.030347545000532588, 0.04232451574608136, 0, 0, 0],
        [0, 0, 0.01302921039494376, 0.01930930643654368, 0, 0, 0],
        [0, 0, 0, 0.0018104302068600111, 0, 0, 0],
        [0, 0, 0, 0, 0.02156951127304255, 0.054121408112153484, 0.0722032100772723],
        [0, 0, 0, 0, 0, 0.015434593934687147, 0.044544566720156394],
        [0, 0, 0, 0, 0, 0, 0.013228271492577652],
        [0, 0, 0, 0, 0, 0, 0],
    ]

    assert dag.prefix_score == [
        1,
        0.010088041794802646,
        0.03047898421955006,
        0.04257448891014735,
        0.0009183109184914482,
        0.0023183650456051422,
        0.003145588490932626,
        0,
    ]

    # TODO: is this correct?
    assert dag.suffix_score == [
        0.012772745230674594,
        0.005695959928025113,
        0.0005324336337048491,
        0.07484515573718929,
        0.04474873971910213,
        0.013228271492577652,
        1,
        0,
    ]
