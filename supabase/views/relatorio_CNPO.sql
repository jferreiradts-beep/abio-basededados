--------------------------------------
-- CONSTRIUIR O RELATÓRIO CNPO MAPA --
--------------------------------------
DROP VIEW IF EXISTS vw_mapa_mapa;

CREATE VIEW vw_mapa_mapa AS
WITH escopo_associado AS (
    -- 1) vínculos excepcionais (rel_ass_esc)
    SELECT
        rae.escopo_id,
        rae.associado_id
    FROM rel_ass_esc rae

    UNION

    -- 2) vínculos por matrícula quando NÃO há vínculos específicos em rel_ass_esc
    SELECT
        e.id          AS escopo_id,
        rma.associado_id
    FROM escopo e
    JOIN uprod u
      ON u.id = e.uprod_id
    JOIN rel_mat_asso rma
      ON rma.matricula_id = u.matricula_id
    WHERE NOT EXISTS (
        SELECT 1
        FROM rel_ass_esc rae2
        WHERE rae2.escopo_id = e.id
    )
),
ultimo_acontecimento_ativo AS (
    SELECT
        a.escopo_id,
        ta.situacao,
        ROW_NUMBER() OVER (
            PARTITION BY a.escopo_id
            ORDER BY a.data DESC
        ) AS rn
    FROM acontecimentos a
    JOIN tipo_acontecimento ta
      ON ta.id = a.tipo_id
    WHERE ta.ordem <> 999
),
ultima_emissao_certificado AS (
    SELECT
        a.escopo_id,
        MAX(a.data) AS data_ultima_emissao
    FROM acontecimentos a
    WHERE a.tipo_id = 1
    GROUP BY a.escopo_id
),
escopo_valido AS (
    SELECT
        uec.escopo_id,
        uec.data_ultima_emissao,
        (uec.data_ultima_emissao
         + INTERVAL '1 year'
         - INTERVAL '1 day') AS data_validade
    FROM ultima_emissao_certificado uec
),
atividades_por_grupo AS (
    SELECT
        rep.escopo_id,
        gp.nome AS grupo_nome,
        CASE WHEN gp.nome = 'Outros' THEN 1 ELSE 0 END AS grupo_ordem,
        gp.nome || ': ' ||
        STRING_AGG(p.nome, ', ' ORDER BY p.nome) AS texto_grupo
    FROM rel_esc_prod rep
    JOIN produtos p
      ON p.id = rep.produto_id
    JOIN grupo_prod gp
      ON gp.id = p.grupo_id
    GROUP BY rep.escopo_id, gp.nome
),
atividades_por_escopo AS (
    SELECT
        ag.escopo_id,
        STRING_AGG(
            ag.texto_grupo,
            E'\n'
            ORDER BY ag.grupo_ordem, ag.grupo_nome
        ) AS atividades
    FROM atividades_por_grupo ag
    GROUP BY ag.escopo_id
)
SELECT
    'OPAC' AS "Tipo de entidade",
    'ASSOCIAÇÃO DE AGRICULTORES BIOLÓGICOS DO ESTADO DO RIO DE JANEIRO' AS "Entidade",
    'BRASIL' AS "Pais",
    est.nome AS "UF",
    mun.nome       AS "Cidade",
    'ATIVO' AS "Situação CNPO",

    CASE
      WHEN length(asso.cpf) = 11 THEN
          substr(asso.cpf,1,3) || '.' ||
          substr(asso.cpf,4,3) || '.' ||
          substr(asso.cpf,7,3) || '-' ||
          substr(asso.cpf,10,2)

      WHEN length(asso.cpf) = 14 THEN
          substr(asso.cpf,1,2) || '.' ||
          substr(asso.cpf,3,3) || '.' ||
          substr(asso.cpf,6,3) || '/' ||
          substr(asso.cpf,9,4) || '-' ||
          substr(asso.cpf,13,2)

      ELSE asso.cpf
    END AS "CPF / CNPJ / NIF",

    asso.nome AS "Nome do produtor",
    te.nome AS "Escopo",
    COALESCE(ae.atividades, '') AS "Atividades",
    asso.contato AS "Contato"
FROM escopo e
JOIN escopo_associado ea
  ON ea.escopo_id = e.id
JOIN associado asso
  ON asso.id = ea.associado_id
JOIN uprod u
  ON u.id = e.uprod_id
JOIN estados est
  ON est.id = u.estado_id
JOIN municipios mun 
  ON mun.id = u.municipio_id  
JOIN tipo_escopo te
  ON te.id = e.nome
JOIN ultimo_acontecimento_ativo ua
  ON ua.escopo_id = e.id
 AND ua.rn = 1
JOIN escopo_valido ev
  ON ev.escopo_id = e.id
LEFT JOIN atividades_por_escopo ae
  ON ae.escopo_id = e.id
WHERE ua.situacao = 'Ativo'
  AND ev.data_validade >= CURRENT_DATE - INTERVAL '30 days';