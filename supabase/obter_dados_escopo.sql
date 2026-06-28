CREATE OR REPLACE FUNCTION public.obter_dados_escopo(p_escopo_id integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_matricula TEXT;
    v_json JSON;
    v_nome_uprod TEXT;
    v_endereco TEXT;
    v_municipio TEXT;
    v_estado TEXT;
    v_tipo_certificado TEXT;
    v_tipo_abreviatura TEXT;
    v_mensagem TEXT;
    v_data_emissao DATE;
BEGIN
    --------------------------------------------------------------------
    -- 1. Buscar dados básicos do escopo + unidade de produção + tipo
    --------------------------------------------------------------------
    SELECT 
        e.matricula,
        u.nome,
        u.endereco,
        u.municipio,
        u.estado,
        te.nome,
        te.abreviatura,
        te.mensagem
    INTO 
        v_matricula,
        v_nome_uprod,
        v_endereco,
        v_municipio,
        v_estado,
        v_tipo_certificado,
        v_tipo_abreviatura,
        v_mensagem
    FROM escopo e
    JOIN uprod u ON u.id = e.uprod_id
    JOIN tipo_escopo te ON te.id = e.nome   -- conforme sua observação
    WHERE e.id = p_escopo_id;

    --------------------------------------------------------------------
    -- 2. Buscar data de emissão (último acontecimento tipo_id = 1)
    --------------------------------------------------------------------
    SELECT a.data
    INTO v_data_emissao
    FROM acontecimentos a
    WHERE a.escopo_id = p_escopo_id
      AND a.tipo_id = 1
    ORDER BY a.data DESC
    LIMIT 1;

    --------------------------------------------------------------------
    -- 3. Buscar associados da matrícula + campo "vinculo"
    --------------------------------------------------------------------
    SELECT json_agg(
               to_jsonb(a) ||
               jsonb_build_object(
                   'vinculo',
                   EXISTS (
                       SELECT 1
                       FROM rel_ass_esc rae
                       WHERE rae.escopo_id = p_escopo_id
                         AND rae.associado_id = a.id
                   )
               )
               ORDER BY a.id
           )
    INTO v_json
    FROM rel_mat_asso r
    JOIN associado a ON a.id = r.associado_id
    WHERE r.matricula = v_matricula;

    --------------------------------------------------------------------
    -- 4. Retornar tudo em um único JSON
    --------------------------------------------------------------------
    RETURN json_build_object(
        'matricula', v_matricula,
        'unidade_producao', v_nome_uprod,
        'endereco', v_endereco,
        'municipio', v_municipio,
        'estado', v_estado,
        'tipo_certificado', v_tipo_certificado,
        'tipo_abreviatura', v_tipo_abreviatura,
        'mensagem', v_mensagem,
        'data_emissao', v_data_emissao,
        'associados', v_json
    );
END;
$function$