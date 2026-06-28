CREATE OR REPLACE FUNCTION public.vincular_associado(p_nome text, p_cpf text, p_matricula text)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_associado_id INTEGER;
BEGIN
    -- 1. Verifica se o CPF já existe
    SELECT id INTO v_associado_id
    FROM associado
    WHERE cpf = p_cpf;

    -- 2. Se não existir, cria o associado
    IF v_associado_id IS NULL THEN
        INSERT INTO associado (nome, cpf)
        VALUES (p_nome, p_cpf)
        RETURNING id INTO v_associado_id;
    END IF;

    -- 3. Cria o vínculo na rel_mat_ass (evita duplicação)
    INSERT INTO rel_mat_asso (matricula, associado_id)
    VALUES (p_matricula, v_associado_id)
    ON CONFLICT DO NOTHING;

    -- 4. Atualiza a materialized view 
    REFRESH MATERIALIZED VIEW vw_dados_com_associado;

    -- 5. Retorna o ID do associado
    RETURN v_associado_id;
END;
$function$