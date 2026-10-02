# Desenha docs/fluxo_paineis.png (System.Drawing, sem dependencias) — fluxo de atualizacao e distribuicao dos paineis DN
Add-Type -AssemblyName System.Drawing
$W = 2000; $H = 1470; $S = 1
$bmp = New-Object System.Drawing.Bitmap($W, $H)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'ClearTypeGridFit'
$g.Clear([System.Drawing.Color]::FromArgb(250, 251, 253))

$fTitle = New-Object System.Drawing.Font('Segoe UI', 22, [System.Drawing.FontStyle]::Bold)
$fLane  = New-Object System.Drawing.Font('Segoe UI', 13, [System.Drawing.FontStyle]::Bold)
$fBoxT  = New-Object System.Drawing.Font('Segoe UI', 11.5, [System.Drawing.FontStyle]::Bold)
$fBox   = New-Object System.Drawing.Font('Segoe UI', 10)
$fSmall = New-Object System.Drawing.Font('Segoe UI', 9)
$cNavy  = [System.Drawing.Color]::FromArgb(23, 55, 110)
$cText  = [System.Drawing.Color]::FromArgb(30, 36, 48)
$cGrey  = [System.Drawing.Color]::FromArgb(95, 105, 120)
$bText  = New-Object System.Drawing.SolidBrush($cText)
$bGrey  = New-Object System.Drawing.SolidBrush($cGrey)
$bNavy  = New-Object System.Drawing.SolidBrush($cNavy)
$pArrow = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(70, 80, 100), 2.2)
$pArrow.CustomEndCap = New-Object System.Drawing.Drawing2D.AdjustableArrowCap(6, 7)
$pDash  = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(150, 160, 175), 1.5); $pDash.DashStyle = 'Dash'

function Box($x, $y, $w, $h, $title, $lines, $fill, $border) {
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $r = 10
    $path.AddArc($x, $y, $r, $r, 180, 90); $path.AddArc($x + $w - $r, $y, $r, $r, 270, 90)
    $path.AddArc($x + $w - $r, $y + $h - $r, $r, $r, 0, 90); $path.AddArc($x, $y + $h - $r, $r, $r, 90, 90); $path.CloseFigure()
    $g.FillPath((New-Object System.Drawing.SolidBrush($fill)), $path)
    $g.DrawPath((New-Object System.Drawing.Pen($border, 1.6)), $path)
    $g.DrawString($title, $fBoxT, $bNavy, ([System.Drawing.RectangleF]::new($x + 12, $y + 8, $w - 24, 26)))
    $yy = $y + 34
    foreach ($l in $lines) {
        $sz = $g.MeasureString($l, $fBox, [int]($w - 24))
        $g.DrawString($l, $fBox, $bText, ([System.Drawing.RectangleF]::new($x + 12, $yy, $w - 24, $sz.Height + 2)))
        $yy += $sz.Height + 1
    }
}
function Lane($x, $y, $w, $h, $title) {
    $g.FillRectangle((New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(238, 242, 248))), $x, $y, $w, $h)
    $g.FillRectangle($bNavy, $x, $y, $w, 38)
    $g.DrawString($title, $fLane, [System.Drawing.Brushes]::White, ([System.Drawing.RectangleF]::new($x + 12, $y + 8, $w - 24, 28)))
}
function Arrow($x1, $y1, $x2, $y2) { $g.DrawLine($pArrow, [float]$x1, [float]$y1, [float]$x2, [float]$y2) }
function Elbow($x1, $y1, $xm, $x2, $y2) { $g.DrawLine($pArrow.Clone(), [float]$x1, [float]$y1, [float]$xm, [float]$y1) ; $g.DrawLine((New-Object System.Drawing.Pen($pArrow.Color, 2.2)), [float]$xm, [float]$y1, [float]$xm, [float]$y2); Arrow $xm $y2 $x2 $y2 }

# ---------------------------------------------------------------- titulo
$g.DrawString('Scorecard DN · como os painéis são atualizados e distribuídos', $fTitle, $bNavy, 40, 22)
$g.DrawString('Estado em 16/09/2026 · Etapa 1 (performance) e Etapa 2 (um painel por usuário, modelo dos painéis Gerenciais) · um comando: python run_dn.py', $fBox, $bGrey, 42, 62)

$cSrc = [System.Drawing.Color]::FromArgb(255, 248, 230); $bSrc = [System.Drawing.Color]::FromArgb(214, 170, 60)
$cStep = [System.Drawing.Color]::White; $bStep = [System.Drawing.Color]::FromArgb(120, 140, 175)
$cOut = [System.Drawing.Color]::FromArgb(232, 246, 236); $bOut = [System.Drawing.Color]::FromArgb(70, 150, 95)
$cUser = [System.Drawing.Color]::FromArgb(236, 238, 250); $bUser = [System.Drawing.Color]::FromArgb(110, 110, 190)
$cLocal = [System.Drawing.Color]::FromArgb(245, 245, 245); $bLocal = [System.Drawing.Color]::FromArgb(150, 150, 150)

# ---------------------------------------------------------------- lanes
Lane 40 100 360 1150 '1 · Fontes (OneDrive · DN/bases)'
Lane 430 100 700 1150 '2 · Pipeline · python run_dn.py (máquina do Douglas, ~7 min)'
Lane 1160 100 420 1150 '3 · Publicação (OneDrive · Painéis Comerciais)'
Lane 1610 100 350 1150 '4 · Quem abre'

# fontes
Box 60 160 320 178 'Sell-through Mtrix (mensal)' @(
 'bases/Sell Out - MTRIX/ScoreCard_Mtrix_MM.AAAA.xlsx',
 '25 arquivos · 10,7 M linhas · distribuidor × PDV × SKU × mês',
 'Rotina: soltar o arquivo do mês (parcial substitui o anterior); no fechamento, soltar a versão fechada') $cSrc $bSrc
Box 60 356 320 190 'Cadastros e de-paras' @(
 'Distribuidores_DePara (CNPJ, nome reduzido, data de cadastro)',
 'Hierarquia_Consolidada (head · gerente · supervisor)',
 'Produtos (categoria) · Clusters_DePara · DE-PARA_Ponderada (carteira)',
 'RTM_DePara_Transicao (clientes e destino)') $cSrc $bSrc
Box 60 566 320 138 'Configuração' @(
 'config/config.yaml: regras, janela de 6 meses, abas, textos, publicação, distribuição por usuário, recursos',
 'template/template.html: layout e JS (prova byte a byte)') $cSrc $bSrc

# pipeline
$px = 450; $pw = 660
$y = 160
$alturas = @{ '0' = 62; '1' = 96; '2' = 138; '2b' = 82; '3' = 114; '4' = 82; '5' = 62; '6' = 300 }
$ys = @{}
foreach ($k in @('0','1','2','2b','3','4','5','6')) { $ys[$k] = $y; $y += $alturas[$k] + 14 }
Box $px $ys['0'] $pw $alturas['0'] '0 · verificar (0 s)' @('manifesto compara md5 das 31 bases: precisa ingerir?') $cStep $bStep
Box $px $ys['1'] $pw $alturas['1'] '1 · ingerir — só quando uma base mudou (1 a 6 min)' @(
 'Excel → staging (cache por arquivo) → curated Parquet: FATO_SELLOUT, DIM_PDV, DIM_DISTRIBUIDOR (com hierarquia), DIM_PRODUTO, DIM_RTM, calendário, gabaritos · relatório de qualidade') $cStep $bStep
Box $px $ys['2'] $pw $alturas['2'] '2 · calcular (55 s)' @(
 'fato com 7 colunas e chaves categóricas (0,97 GB) → pares mês × distribuidor × PDV (× categoria) e base ativa uma vez',
 '→ 14 cubos nível × mês (canal, segmento, supervisor, cluster, distribuidor, × categoria) → acumulados → RTM → base ativa de PDVs → carteira → penetração',
 'calibração da frequência guardada por ingestão') $cStep $bStep
Box $px $ys['2b'] $pw $alturas['2b'] '2b · mês fechado (19 s)' @('com o mês em andamento: base ativa, carteira, máscara, penetração e RTM refeitos para o último mês fechado (pares cortados)') $cStep $bStep
Box $px $ys['3'] $pw $alturas['3'] '3 · renderizar (44 s)' @(
 'JSON do mês de referência + mês fechado + 23 meses leves (índices por cubo) → pacotes gzip por mês → formatação pt-BR pelo inventário → Handlebars mínimo → HTML único offline de 14,9 MB',
 'gravado em %LOCALAPPDATA%\Dori\DN\painel (fora do OneDrive)') $cStep $bStep
Box $px $ys['4'] $pw $alturas['4'] '4 · validar (29 s)' @('120 conferências: cards = fato, cubos, pacotes, lista de PDVs, acumulados, RTM, frequência, template · falha = PIPELINE ABORTADO, nada publicado') $cStep $bStep
Box $px $ys['5'] $pw $alturas['5'] '5 · publicar o canal' @('cópia atômica (.tmp → replace) com md5 conferido · nada copiado se o md5 não mudou') $cStep $bStep
Box $px $ys['6'] $pw $alturas['6'] '6 · distribuir — um painel por usuário (5 min, 18 usuários)' @(
 'usuários descobertos da hierarquia em DIM_DISTRIBUIDOR: N1 head (1) · N2 gerentes (3) · N3 supervisores (14); nada de lista para manter',
 'para cada usuário: FATO recortada aos distribuidores dele ANTES de qualquer cubo → mesmo cálculo e mesma renderização do canal (referência da Penetração = canal; RTM só com destinos do recorte; carteira só do recorte)',
 '12 conferências essenciais + busca de vazamento no código-fonte (rótulos, nomes, códigos e slugs dos outros usuários; CNPJ e nome dos distribuidores fora da carteira) = 0 ocorrências',
 'soma dos gerentes e dos supervisores = canal (kg, R$, NFs, por categoria); PDVs distintos: máx ≤ canal ≤ soma',
 'N1 = cópia byte a byte do canal · falha em um usuário não interrompe os outros (em_erro: continuar | abortar_publicacao | parar)',
 'gravação local em ...\painel\usuarios\<slug>\ · publicação atômica por usuário, só quando o md5 muda') $cStep $bStep

# publicacao
Box 1180 160 380 150 'Painéis Comerciais/DN/' @(
 'Scorecard_DN.html — painel do canal inteiro',
 '14,9 MB · set/26 parcial + ago/26 fechado + 25 meses',
 'compartilhar a pasta com pessoas específicas, Pode exibir') $cOut $bOut
Box 1180 340 380 300 'Painéis Comerciais/Gerencial/<rótulo>/' @(
 'Scorecard_DN_N<nível>_<slug>.html (nome estável para links)',
 'pasta = rótulo da hierarquia: "1120 - Superv_SPC - CAIO LUPERNI" ("/" vira "-"); as mesmas pastas dos painéis Gerenciais',
 'N1 · 10 - DISTRIBUICAO - MICHEL MEIRA (cópia do canal, 14,9 MB)',
 'N2 · 11000 Sudeste · 12000 CO/SUL · 13000 NO/NE (5 a 7 MB)',
 'N3 · 14 supervisores, 1110 a 1340 (0,6 a 3 MB)',
 'cada arquivo contém só a carteira do usuário: dropdown, tabelas, pacotes, blob de PDVs e RTM') $cOut $bOut
Box 1180 670 380 130 'Só o resultado final no OneDrive' @(
 'JSON e HTML de trabalho ficam locais; o OneDrive sincroniza só o que mudou',
 'logs e resumo por execução em data/dn/logs (etapas, usuários, md5, erros)') $cLocal $bLocal

# usuarios
Box 1630 160 310 130 'Michel Meira (head)' @('painel do canal: todos os supervisores e distribuidores', 'abre o HTML no Chrome/Edge, offline') $cUser $bUser
Box 1630 340 310 130 'Gerentes regionais (3)' @('só a regional: seus supervisores e distribuidores', 'pasta do gerente') $cUser $bUser
Box 1630 500 310 140 'Supervisores (14)' @('só a carteira: 2 a 9 distribuidores', 'ex.: Caio Luperni, 4 distribuidores, 7.816 PDVs na base ativa, 2,1 MB') $cUser $bUser
Box 1630 670 310 130 'Regra' @('compartilhamento por pasta, Pode exibir, nunca "qualquer pessoa com o link" (CNPJ, razão social e endereço embutidos)') $cUser $bUser

# setas
Arrow 380 249 450 190
Arrow 380 451 450 280
Arrow 380 635 450 390
foreach ($k in @('0','1','2','2b','3','4','5')) { $yb = $ys[$k] + $alturas[$k]; Arrow ($px + 330) $yb ($px + 330) ($yb + 14) }
Arrow 1110 ($ys['5'] + 31) 1180 235
Arrow 1110 ($ys['6'] + 150) 1180 490
Arrow 1560 235 1630 225
Arrow 1560 420 1630 405
Arrow 1560 520 1630 570
$g.DrawLine($pDash, 1110, ($ys['3'] + 100), 1180, 735)

# rodape
$g.DrawString('Tempos medidos em 16/09/2026 (canal 2 min + usuários 5 min; era ~17 a 30 min antes da Etapa 1). Nada é publicado com validação pendente. Regras: docs/regras_negocio.md (RN-60 a RN-64) · docs/performance_etapa1.md · docs/distribuicao_etapa2.md', $fSmall, $bGrey, 42, 1270)
$g.DrawString('Comandos: python run_dn.py (tudo) · --sem-publicar · --usuario 1120 · --sem-usuarios · --forcar · --regerar-exemplo', $fSmall, $bGrey, 42, 1292)

$out = 'C:\Users\dldsouza\OneDrive - Dori Alimentos S.A\Documentos\PAINÉIS - SCORECARDS\Painéis - Alavancas\DN\docs\fluxo_paineis.png'
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
"gravado: $out ($([math]::Round((Get-Item $out).Length/1KB)) KB)"
