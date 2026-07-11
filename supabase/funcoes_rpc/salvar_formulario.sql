CREATE OR REPLACE FUNCTION public.salvar_formulario(p_tabela text, p_dados jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    -- ✅ 1. COALESCE para tratar id NULL como 0 (novo registro)
    v_id   int   := COALESCE((p_dados->'dados_fixos'->>'id')::int, 0);
    v_fixos jsonb := p_dados->'dados_fixos';
    v_aj    jsonb := p_dados->'dados_ajustaveis';
    v_sql   text;
BEGIN
    IF v_fixos IS NULL THEN
         RETURN jsonb_build_object('status', 'error', 'message', 'Dados fixos inválidos.');
    END IF;

    IF v_id = 0 THEN
        
        -- ✅ 2. INSERT: converter strings vazias em NULL
        SELECT format(
            'INSERT INTO %I (%s) VALUES (%s) RETURNING id',
            p_tabela,
            string_agg(quote_ident(key), ','),
            string_agg(
                CASE WHEN value IS NULL OR value = '' THEN 'NULL'
                     ELSE quote_nullable(value)
                END, ','
            )
        )
        INTO v_sql
        FROM jsonb_each_text(v_fixos)
        WHERE key <> 'id';

        EXECUTE v_sql INTO v_id;

    ELSE
        
        -- ✅ 3. UPDATE: converter strings vazias em NULL
        SELECT format(
            'UPDATE %I SET %s WHERE id = %L',
            p_tabela,
            string_agg(
                format('%I = %s', key, 
                    CASE WHEN value IS NULL OR value = '' THEN 'NULL'
                         ELSE quote_literal(value)
                    END
                ), ','
            ),
            v_id
        )
        INTO v_sql
        FROM jsonb_each_text(v_fixos)
        WHERE key <> 'id';

        IF v_sql IS NOT NULL THEN
            EXECUTE v_sql;
        END IF;

        EXECUTE format(
            'DELETE FROM info_%I WHERE %I_id = %L',
            p_tabela,
            p_tabela,
            v_id
        );

    END IF;

    EXECUTE format(
        'INSERT INTO info_%I (%I_id, campo_id, valor)
         SELECT $1, (x->>''campo_id'')::int, x->>''valor''
         FROM jsonb_array_elements($2) x
         WHERE (x->>''campo_id'') ~ ''^[0-9]+$'' ',
        p_tabela,
        p_tabela
    )
    USING v_id, v_aj;

    -- Atualiza a materialized view 
    REFRESH MATERIALIZED VIEW vw_dados_com_associado;

    RETURN jsonb_build_object('status', 'success', 'id', v_id);

EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object('status', 'error', 'message', SQLERRM);
END;
$function$
