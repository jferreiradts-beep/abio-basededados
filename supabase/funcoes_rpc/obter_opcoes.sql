)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    lista_opcoes jsonb;

    v_tabela text;          -- tabela base (metadados.tabela)
    v_tabela_opcoes text;   -- tabela de opções (metadados_opcoes.tabela)
    v_coluna_retorno text;
    v_coluna_filtro text;
    v_tipo text;

    v_tabela_avo text;
    v_filtro integer;
BEGIN
    ----------------------------------------------------------------------
    -- 1. Buscar metadados
    ----------------------------------------------------------------------
    SELECT m.tabela, o.tabela, o.coluna_retorno, o.coluna_filtro, o.tipo
    INTO v_tabela, v_tabela_opcoes, v_coluna_retorno, v_coluna_filtro, v_tipo
    FROM metadados m
    JOIN metadados_opcoes o ON o.campo_id = m.id
    WHERE m.id = idx;

    IF v_tabela IS NULL THEN
        RAISE EXCEPTION 'Nenhuma configuração de opções encontrada para campo_id=%', idx;
    END IF;

    ----------------------------------------------------------------------
    -- 2. Determinar o filtro real
    ----------------------------------------------------------------------
    IF p_filtro IS NULL THEN
        v_filtro := NULL;

    ELSIF v_tipo = 'ascendente' THEN
        ------------------------------------------------------------------
        -- Buscar o pai na tabela base (v_tabela)
        ------------------------------------------------------------------    

        SELECT tab_pai INTO v_tabela_avo 
        FROM metadados_hierarquia
        WHERE tabela = v_tabela_opcoes;

        EXECUTE FORMAT(
            'SELECT %I_id FROM %I WHERE id = $1',
            v_tabela_avo, v_tabela_opcoes
        ) INTO v_filtro USING p_filtro;

        IF v_filtro IS NULL THEN
            RAISE EXCEPTION 'Registro % não possui pai na tabela %', p_filtro, v_tabela;
        END IF;

    ELSE
        v_filtro := p_filtro;
    END IF;

    ----------------------------------------------------------------------
    -- 3. Montar SQL dinâmico (igual ao seu)
    ----------------------------------------------------------------------
    IF v_coluna_filtro IS NOT NULL THEN
        EXECUTE FORMAT(
            'SELECT jsonb_agg(jsonb_build_object(''id'', id, ''opcao'', %I))
             FROM %I
             WHERE %I = $1',
            v_coluna_retorno, v_tabela_opcoes, v_coluna_filtro
        ) INTO lista_opcoes USING v_filtro;

    ELSE
        EXECUTE FORMAT(
            'SELECT jsonb_agg(jsonb_build_object(''id'', id, ''opcao'', %I))
             FROM %I',
            v_coluna_retorno, v_tabela_opcoes
        ) INTO lista_opcoes;
    END IF;

    RETURN COALESCE(lista_opcoes, '[]'::jsonb);
END;
$function$
