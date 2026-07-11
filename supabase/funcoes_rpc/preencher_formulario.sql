CREATE OR REPLACE FUNCTION public.preencher_formulario(p_tabela text, p_registro integer)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    dados_fixos jsonb;
    dados_ajustaveis jsonb;
    campos_fixos jsonb;
    campos_ajustaveis jsonb;
BEGIN
    -- 1. Campos fixos:
    SELECT jsonb_object_agg(
        campo, jsonb_build_object(
            'id', m.id,
            'ordem', m.ordem,
            'rotulo', m.rotulo,
            'mascara', m.mascara,
            'opcoes', m.opcoes,
            'filtro', f.campo_filtro))
    INTO campos_fixos
    FROM metadados m
    LEFT JOIN metadados_opcoes f ON f.campo_id = m.id
    WHERE m.tabela = p_tabela;

    -- 2. Campos ajustáveis
    EXECUTE FORMAT (
        'SELECT jsonb_agg(jsonb_build_object(''id'', id, ''nome'', nome))
         FROM campos_%I', p_tabela
    ) INTO campos_ajustaveis;

    -- 3. Dados fixos
    IF p_registro = 0 THEN
        -- Template vazio
        SELECT jsonb_object_agg(campo, NULL)
        INTO dados_fixos
        FROM metadados m
        WHERE m.tabela = p_tabela;

        dados_ajustaveis := '[]'::jsonb;

    ELSE
        -- Dados fixos
        EXECUTE FORMAT(
            'SELECT to_jsonb(t)
             FROM %I t WHERE id = $1', p_tabela
        ) INTO dados_fixos USING p_registro;

        -- Dados ajustáveis
        EXECUTE FORMAT (
            'SELECT jsonb_agg(jsonb_build_object(''id'', id, ''campo_id'', campo_id, ''valor'', valor))
             FROM info_%I WHERE %I_id = $1', p_tabela, p_tabela
        ) INTO dados_ajustaveis USING p_registro;

    END IF;

    -- 

    -- 6. Retorno final
    RETURN jsonb_build_object(
        'dados_fixos', dados_fixos,
        'dados_ajustaveis', COALESCE(dados_ajustaveis, '[]'::jsonb),
        'campos_fixos', COALESCE(campos_fixos, '[]'::jsonb),
        'campos_ajustaveis', COALESCE(campos_ajustaveis, '[]'::jsonb)
    );
END;
$function$
