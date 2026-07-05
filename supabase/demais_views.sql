DROP VIEW IF EXISTS vw_escopo_cpf_visivel;
CREATE VIEW vw_escopo_cpf_visivel AS
SELECT
    e.id AS id_escopo,
    a.id,
    a.cpf
FROM escopo e
JOIN rel_mat_asso rma ON rma.matricula = e.matricula
JOIN associado a ON a.id = rma.associado_id
WHERE rma.associado_id NOT IN (
    SELECT rea.associado_id
    FROM rel_ass_esc rea
    WHERE rea.escopo_id != e.id
      AND rea.escopo_id IN (
          SELECT id FROM escopo WHERE matricula = e.matricula
      )
);

-- Criar a View que relaciona Associados a Grupos
CREATE OR REPLACE VIEW vw_associados_por_grupo AS
SELECT a.id, a.nome, m.grupo_id
FROM associado a
JOIN rel_mat_asso rma ON rma.associado_id = a.id
JOIN matriculas m ON m.matricula = rma.matricula;

-- Criar a View que relaciona Matrículas a Unidades de produçao
CREATE OR REPLACE VIEW vw_uprod_por_matricula AS
SELECT DISTINCT uprod.id, uprod.nome, e2.id AS escopo_id
FROM escopo e1
JOIN escopo e2 ON e1.matricula = e2.matricula
JOIN uprod ON e1.uprod_id = uprod.id
ORDER BY uprod.id, e2.id
