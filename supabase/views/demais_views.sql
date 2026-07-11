----------------------------
-- CONSTRUIR DEMAIS VIEWS --
----------------------------

-- 1. Lista de associados por escopo
DROP VIEW IF EXISTS vw_escopo_cpf_visivel;
CREATE VIEW vw_escopo_cpf_visivel AS
SELECT
    e.id AS id_escopo,
    a.id AS id_associado
FROM escopo e
JOIN uprod u ON u.id = e.uprod_id
JOIN rel_mat_asso rma ON rma.matricula_id = u.matricula_id
JOIN associado a ON a.id = rma.associado_id
WHERE rma.associado_id NOT IN (
    SELECT rea.associado_id
    FROM rel_ass_esc rea
    WHERE rea.escopo_id != e.id
      AND rea.escopo_id IN (
        SELECT sub_e.id 
        FROM escopo sub_e
        JOIN uprod sub_u ON sub_u.id = sub_e.uprod_id
        WHERE sub_u.matricula_id = u.matricula_id
      )
);

-- 2. Relaciona associados a grupos p/ dropdown de coordenador
DROP VIEW vw_associados_por_grupo;
CREATE OR REPLACE VIEW vw_associados_por_grupo AS
SELECT a.id, a.nome, m.grupo_id
FROM associado a
JOIN rel_mat_asso rma ON rma.associado_id = a.id
JOIN matricula m ON m.id = rma.matricula_id;