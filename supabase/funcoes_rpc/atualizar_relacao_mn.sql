CREATE OR REPLACE FUNCTION public.atualizar_relacao_nm(p_tabela text, p_coluna_fixa text, p_valor_fixo integer, p_ids_opostos integer[])
 RETURNS void
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_coluna_oposta TEXT;
    v_sql TEXT;
    p_valor INT;
BEGIN
    -- 1. Descobrir automaticamente a outra coluna (a que não é a fixa)
    SELECT column_name
    INTO v_coluna_oposta
    FROM information_schema.columns
    WHERE table_name = p_tabela
      AND column_name <> p_coluna_fixa
      AND column_name LIKE '%\_id' ESCAPE '\'
    LIMIT 1;

    IF v_coluna_oposta IS NULL THEN
        RAISE EXCEPTION 'Não foi possível identificar a coluna oposta na tabela %', p_tabela;
    END IF;

    -- 2. Apagar todas as linhas existentes para o valor fixo
    v_sql := format(
        'DELETE FROM %I WHERE %I = $1',
        p_tabela, p_coluna_fixa
    );
    EXECUTE v_sql USING p_valor_fixo;

    -- 3. Inserir novas linhas
    v_sql := format(
        'INSERT INTO %I (%I, %I) VALUES ($1, $2)',
        p_tabela, p_coluna_fixa, v_coluna_oposta
    );

    FOREACH p_valor IN ARRAY p_ids_opostos LOOP
        EXECUTE v_sql USING p_valor_fixo, p_valor;
    END LOOP;

END;
$function$
