CREATE OR REPLACE FUNCTION public.obter_produtos(p_escopo_id integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_json JSON;
BEGIN
    SELECT json_object_agg(
               tipo_id,
               grupos_lista
           )
    INTO v_json
    FROM (
        SELECT 
            id AS tipo_id,
            json_agg(
                json_build_object(
                    'grupo', grupo_nome,
                    'produtos', produtos_json
                )
                ORDER BY grupo_nome
            ) AS grupos_lista
        FROM (
            SELECT 
                te.id,
                gp.nome AS grupo_nome,
                json_agg(pr.nome ORDER BY pr.nome) AS produtos_json
            FROM rel_esc_prod rep
            JOIN produtos pr ON pr.id = rep.produto_id
            JOIN grupo_prod gp ON gp.id = pr.grupo_id
            JOIN tipo_escopo te ON te.id = gp.tipo_escopo_id
            WHERE rep.escopo_id = p_escopo_id
            GROUP BY te.id, gp.nome
        ) sub
        GROUP BY tipo_id
    ) final;

    RETURN v_json;
END;
$function$
