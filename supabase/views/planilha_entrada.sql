---------------------------------
-- RECRIAR PLANILHA DE ENTRADA --
---------------------------------

DROP MATERIALIZED VIEW IF EXISTS vw_dados_com_associado;
CREATE MATERIALIZED VIEW vw_dados_com_associado AS
    SELECT
        n.id AS id_nucleo,
        n.nome AS nucleo,
        g.id AS id_grupo,
        g.nome AS grupo,
        m.id AS id_matricula,
        m.nome AS matricula,

        -- Primeiro associado via rel_mat_asso
        (
            SELECT a.nome
            FROM rel_mat_asso r
            JOIN associado a ON a.id = r.associado_id
            WHERE r.matricula_id = m.id
            ORDER BY a.id
            LIMIT 1
        ) AS primeiro_associado,

        u.id AS id_uprod,
        u.nome AS uprod,

        e.id AS id_escopo,
        te.abreviatura ||
        COALESCE( NULLIF('-' || TRIM(e.complemento), '-'), '' ) AS escopo,
        mun.nome AS municipio,
        est.nome AS estado,

        -- Nova lógica de validade
        (
            SELECT (a.data + (e.val_duracao || ' months')::INTERVAL - INTERVAL '1 day')::DATE
            FROM acontecimentos a
            WHERE a.escopo_id = e.id AND a.tipo_id = 1
            ORDER BY a.data DESC
            LIMIT 1
        ) AS validade,

            -- NOVA COLUNA: último situação (qualquer tipo)
        (
            SELECT ta.situacao
            FROM acontecimentos a
            JOIN tipo_acontecimento ta ON ta.id = a.tipo_id
            WHERE a.escopo_id = e.id
            AND a.tipo_id <> 8
            ORDER BY a.data DESC
            LIMIT 1
        ) AS ultima_situacao
    FROM
        nucleo n
    LEFT JOIN grupo g ON g.nucleo_id = n.id
    LEFT JOIN matricula m ON m.grupo_id = g.id
    LEFT JOIN uprod u ON u.matricula_id = m.id
    LEFT JOIN estados est ON est.id = u.estado_id
    LEFT JOIN municipios mun ON mun.id = u.municipio_id
    LEFT JOIN escopo e ON e.uprod_id = u.id
    LEFT JOIN tipo_escopo te ON te.id = e.nome;

CREATE UNIQUE INDEX idx_vw_dados_com_associado_escopo
ON vw_dados_com_associado (id_escopo);