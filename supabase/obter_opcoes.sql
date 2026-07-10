CREATE OR REPLACE FUNCTION public.obter_opcoes(idx integer, p_filtro integer)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    lista_opcoes jsonb;

    v_campo_nome text;      -- nome do campo (metadados.campo)
    v_tabela text;          -- tabela base (metadados.tabela)
    v_tabela_opcoes text;   -- tabela de opções (metadados_opcoes.tabela)
    v_coluna_retorno text;
    v_coluna_filtro text;
    v_tipo text;

    v_child_id integer;
    v_filtro integer;
BEGIN
    ----------------------------------------------------------------------
    -- 1. Buscar metadados
    ----------------------------------------------------------------------
    SELECT m.campo, m.tabela, o.tabela, o.coluna_retorno, o.coluna_filtro, o.tipo
    INTO v_campo_nome, v_tabela, v_tabela_opcoes, v_coluna_retorno, v_coluna_filtro, v_tipo
    FROM metadados m
    JOIN metadados_opcoes o ON o.campo_id = m.id
    WHERE m.id = idx;

    IF v_tabela IS NULL THEN
        RAISE EXCEPTION 'Nenhuma configuração de opções encontrada para campo_id=%', idx;
    END IF;

    ----------------------------------------------------------------------
    -- 2. Determinar o filtro real
    ----------------------------------------------------------------------
    IF p_filtro IS NULL OR p_filtro = 0 THEN
        v_filtro := NULL;

    ELSIF v_tipo = 'ascendente' THEN
        ------------------------------------------------------------------
        -- Buscar o pai na tabela base (v_tabela)
        ------------------------------------------------------------------
        -- p_filtro é o ID do registro na tabela base (ex: id de escopo).
        -- Primeiro, pegamos o valor da coluna (ex: uprod_id) no registro atual.
        EXECUTE FORMAT(
            'SELECT %I FROM %I WHERE id = $1',
            v_campo_nome, v_tabela
        ) INTO v_child_id USING p_filtro;

        IF v_child_id IS NULL THEN
            v_filtro := NULL;
        ELSE
            -- Agora, buscamos o pai na tabela de opções (ex: matricula_id em uprod)
            EXECUTE FORMAT(
                'SELECT %I FROM %I WHERE id = $1',
                v_coluna_filtro, v_tabela_opcoes
            ) INTO v_filtro USING v_child_id;
        END IF;

    ELSE
        v_filtro := p_filtro;
    END IF;

    ----------------------------------------------------------------------
    -- 3. Montar SQL dinâmico
    ----------------------------------------------------------------------
    IF v_coluna_filtro IS NOT NULL AND v_filtro IS NOT NULL THEN
        EXECUTE FORMAT(
            'SELECT jsonb_agg(jsonb_build_object(''id'', id, ''opcao'', %I))
             FROM %I
             WHERE %I = $1',
            v_coluna_retorno, v_tabela_opcoes, v_coluna_filtro
        ) INTO lista_opcoes USING v_filtro;

    ELSE
        -- Se não há filtro ou o valor do filtro é NULL, retorna todas as opções
        EXECUTE FORMAT(
            'SELECT jsonb_agg(jsonb_build_object(''id'', id, ''opcao'', %I))
             FROM %I',
            v_coluna_retorno, v_tabela_opcoes
        ) INTO lista_opcoes;
    END IF;

    RETURN COALESCE(lista_opcoes, '[]'::jsonb);
END;
$function$;
