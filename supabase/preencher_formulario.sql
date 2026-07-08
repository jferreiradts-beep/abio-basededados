CREATE OR REPLACE FUNCTION public.preencher_formulario(p_tabela text, p_registro integer)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    dados_fixos jsonb;
    dados_ajustaveis jsonb;
    campos_fixos jsonb;
    campos_ajustaveis jsonb;
    v_subtitulo text := 'SPG ABIO';
    r_view record;
    v_ancestrais text[];
    v_view_json jsonb;
    v_anc text;
    v_val text;
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

        -- 4. Subtítulo dinâmico baseado na tabela de hierarquia e na view
        IF p_tabela <> 'nucleo' THEN
            -- 4.1. Encontrar o registro correspondente na view
            IF p_tabela = 'associado' THEN
                SELECT * INTO r_view
                FROM vw_dados_com_associado
                WHERE id_matricula = (
                    SELECT matricula_id 
                    FROM rel_mat_asso 
                    WHERE associado_id = p_registro 
                    LIMIT 1
                )
                LIMIT 1;
            ELSE
                EXECUTE format(
                    'SELECT * FROM vw_dados_com_associado WHERE id_%I = $1 LIMIT 1',
                    p_tabela
                ) INTO r_view USING p_registro;
            END IF;

            -- 4.2. Se encontramos a linha, construir a árvore de ancestrais
            IF r_view IS NOT NULL THEN
                -- Obter a lista de antepassados ordenados do topo para a base (ex: nucleo, grupo, matricula...)
                WITH RECURSIVE h AS (
                    SELECT tab_pai, 1 AS level
                    FROM metadados_hierarquia
                    WHERE tabela = p_tabela
                    
                    UNION ALL
                    
                    SELECT mh.tab_pai, h.level + 1
                    FROM metadados_hierarquia mh
                    JOIN h ON h.tab_pai = mh.tabela
                )
                SELECT array_agg(tab_pai ORDER BY level DESC)
                INTO v_ancestrais
                FROM h;

                -- 4.3. Montar a string dinamicamente convertendo o record para jsonb
                v_view_json := to_jsonb(r_view);
                FOREACH v_anc IN ARRAY v_ancestrais LOOP
                    v_val := v_view_json->>v_anc;
                    IF v_val IS NOT NULL AND v_val <> '' THEN
                        v_subtitulo := v_subtitulo || ' - ' || v_val;
                    END IF;
                END LOOP;
            END IF;
        END IF;

    END IF;

    -- 6. Retorno final
    RETURN jsonb_build_object(
        'dados_fixos', dados_fixos,
        'dados_ajustaveis', COALESCE(dados_ajustaveis, '[]'::jsonb),
        'campos_fixos', COALESCE(campos_fixos, '[]'::jsonb),
        'campos_ajustaveis', COALESCE(campos_ajustaveis, '[]'::jsonb),
        'subtitulo', v_subtitulo
    );
END;
$function$
