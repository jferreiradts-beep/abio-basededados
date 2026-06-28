CREATE OR REPLACE FUNCTION public.eliminar_e_atualizar(p_tabela text, p_coluna text, p_id text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
DECLARE
    comando_sql TEXT;
BEGIN
    -- Monta o comando DELETE de forma segura
    comando_sql := format(
        'DELETE FROM %I WHERE %I = $1',
        p_tabela,
        p_coluna
    );

    -- Executa o DELETE
    EXECUTE comando_sql USING p_id;

    -- Atualiza a materialized view
    REFRESH MATERIALIZED VIEW vw_dados_com_associado;
END;
$function$