#!/usr/bin/perl

#************************************************************************
# Monjo-Hakase PROGRAM START
#************************************************************************

#========================================================================
# グローバル定数
#========================================================================
#真偽
$cgFALSE=0;
$cgTRUE=1;

#メッセージキーワード
$cgKWD_START_WORD="\`";                         #文節開始クォーテーション
$cgKWD_END_WORD="\'";                           #文節終了クォーテーション
$cgKWD_ARROW=' -> ';                            #矢印
$cgKWD_ARROW2='＞＞';                           #矢印(インデント用)
$cgKWD_SUBJECT='**** misssing subject for ';    #主語なし
$cgKWD_AVOID1='**** avoid using ';              #冗長表現１
$cgKWD_AVOID2='(instead use ';                  #冗長表現２
$cgKWD_REVERSED='**** reversed word order ';    #語順エラー
$cgKWD_PHRASE1='**** too long phrase (should be <= ';      #文節長さ超過
$cgKWD_PHRASE2=' chars)';
$cgKWD_SENTENCE1='**** too long sentence (should be <=';   #１文長さ超過
$cgKWD_SENTENCE2=' chars)';

#エラー種別
$cgERR_SUBJECT=1;       #主語なし
$cgERR_AVOID=2;         #冗長表現
$cgERR_REVERSED=3;      #語順エラー
$cgERR_PHRASE=4;        #文節長さ超過
$cgERR_SENTENCE=5;      #１文長さ超過
$cgERR_CONNECTION=6;    #係り受け量過多
$cgERR_CHAIN=7;         #係り受け長さ冗長

#エラー種別（表示文言）
@cgaERR_TYPE=("","主語なし","冗長表現","語順エラー","文節長さ超過","１文長さ超過",
                 "係り受け量過多","係り受け長さ冗長");

#文節長さ超過のメッセージ
$cgMSG_PHRASE1="文節の長い箇所があります。（";
$cgMSG_PHRASE2="文字以上）";

#１文長さ超過のメッセージ
$cgMSG_SENTENCE1="１文の長さが長すぎます。（";
$cgMSG_SENTENCE2="文字以上）";

#エラーの解説
$cgCMNT_SUBJECT_TITLE="　＜主語なし＞";
@cgaCMNT_SUBJECT=(
    "主語がないときにこのエラーが発生します。文章を訂正し、主語を明確にしましょう。",
    "なお、主語と考えられる文章直後の読点を抜いて再校正してもこのエラーが発生する場合、",
    "係り受け解析では主語が検出できなかったことになります。"
);
$cgCMNT_AVOID_TITLE="　＜冗長表現＞";
@cgaCMNT_AVOID=(
    "冗長的な表現についてのエラーです。推奨される訂正例が機械的に提示されます。",
    "接続詞を見てエラーを判定しているため、たまに解析を誤ることがありますが、",
    "説明文では明確な表現をすることが正解であるため、誤検出であっても言い回しを変更し、",
    "校正することが望ましいです。"
);
$cgCMNT_REVERSED_TITLE="　＜語順エラー＞";
@cgaCMNT_REVERSED=(
    "語順に問題があるというエラーです。",
    "「……が（は）…… を……から……に……する」という語順でなければエラーを表示します。",
    "語順が入れ替わっても日本語として間違いではありません。",
    "しかしより分かりやすい技術文書とするため、この順番に従うことを推奨します。"
);
$cgCMNT_PHRASE_TITLE="　＜文節長さ超過＞";
@cgaCMNT_PHRASE=(
    "文節の長さが長すぎる時にこのエラーが発生します。読点で文節を分割するか、より簡潔にしましょう。",
    "英単語の文字数も1文字としてカウントされるため、あくまで目安と考えてください。"
);
$cgCMNT_SENTENCE_TITLE="　＜１文長さ超過＞";
@cgaCMNT_SENTENCE=(
    "1文の長さが長すぎるときこのエラーが発生します。文章を2つ以上に分割するか、より簡潔にしましょう。",
    "英単語の文字数も1文字としてカウントされるため、あくまで目安と考えてください。"
);
$cgCMNT_CONNECTION_TITLE="　＜係り受け量過多＞";
@cgaCMNT_CONNECTION=(
    "係り受ける文節が、係り受け先に対し5つ以上係り受けたときこのエラーが発生します。",
    "文法的に間違いではありませんが、誤読を招く為4つ以下にしましょう。"
);
$cgCMNT_CHAIN_TITLE="　＜係り受け長さ冗長＞";
@cgaCMNT_CHAIN=(
    "係り受けの長さが、係り受け先を含め5段以上になったときこのエラーが発生します。",
    "可能なかぎり係り受けの長さは4段以下にしましょう。"
);

# 閾値
$cgBOUNDARY_CONNECTION=5;    #係り受け量過多閾値(5つ以上)
$cgBOUNDARY_CHAINING=5;      #係り受け冗長閾値(4段以上)

#========================================================================
# グローバル変数
#========================================================================
@gaStatement=();     #文
@gaCSSStatement=();  #書式付き文
@gaErrorCnt=();      #文ごとのエラー件数
@gaError=();         #文ごとのエラー情報(文番号,エラー種別,エラー箇所,対象文節)
%ghError=(
    $cgERR_SUBJECT    => $cgFALSE,
    $cgERR_AVOID      => $cgFALSE,
    $cgERR_REVERSED   => $cgFALSE,
    $cgERR_PHRASE     => $cgFALSE,
    $cgERR_SENTENCE   => $cgFALSE,
    $cgERR_CONNECTION => $cgFALSE,
    $cgERR_CHAIN      => $cgFALSE 
);                  #エラー有無
%ghClass=(
    $cgERR_SUBJECT    => 'error-missing-subject',
    $cgERR_AVOID      => 'error-avoid-using',
    $cgERR_REVERSED   => 'reversed-word-order',
    $cgERR_PHRASE     => '',
    $cgERR_SENTENCE   => '',
    $cgERR_CONNECTION => 'too-many-connection',
    $cgERR_CHAIN      => 'too-long-chaining'
);                  #エラーに対するクラス名
$gTopReturnCnt=0;   #入力文字列の先頭の改行数

#************************************************************************
# SUB ROUTINE : 改行タグの挿入処理
#   引数１：挿入対象の文章
#   引数２：改行直前の文章
#   引数３：挿入するBRタグ
#************************************************************************
sub subInsBr($$$) {
    ### 変数 ###
    my $pLine;         #挿入対象の文章
    my $pStatement;    #改行直前の文章
    my $pBr;           #改行タグ
    my @paWkLine=();   #文章加工の作業用領域
    my @paWkEdit=();   #文章加工の作業用領域
    my $pWkTxt;        #作業用領域
    my $pI;            #添字

    $pLine=$_[0];
    $pStatement=$_[1];
    $pBr=$_[2];

    ### 挿入対象の文章を、挿入したタグで分割する ###
    $pWkTxt=$pLine;
    $pWkTxt =~ s/\>/\>\n/g;
    @paWkLine=split(/\n/,$pWkTxt);

    ### 分割した文章で改行直前の文章を検索する ###
    for ($pI=0; $pI<=$#paWkLine; $pI++) {
        #=== タグの始端直前の文章を取得する ===
        $pWkTxt=$paWkLine[$pI];
        $pWkTxt =~ s/\</\n\</;
        @paWkEdit=split(/\n/,$pWkTxt);

        #=== 改行直前の文章と比較する ===
        if (($paWkEdit[0] =~ m/$pStatement/s) eq $cgTRUE) {
            #--- 改行直前の文章が含まれる場合は検索終了 ---
            last;
        } else {
            #--- 改行直前の文章が含まれない場合は改行直前の文章を加工 ---
            $pStatement =~ s/$paWkEdit[0]//sx;
        }
    }

    ### 挿入対象の文章を改行直前の文章にタグを付加値で置換する ###
    $pWkTxt=join('',$pStatement,$pBr);
    $pLine =~ s/$pStatement/$pWkTxt/xs;

    # 変数のクリア
    @paWkLine=();
    @paWkEdit=();

    return $pLine;
}

#************************************************************************
# SUB ROUTINE : 本文への改行の復元
#   引数１：入力の文章(JCorrect実行元の文章)
#************************************************************************
sub subEditBR($) {
    ### 変数 ###
    my $pStatement;      #入力の文章
    my $pBr;             #改行タグ
    my @paWkState=();    #文章加工の作業用領域
    my @paWkEdit=();     #文章加工の作業用領域
    my @paWkEdit2=();    #文章加工の作業用領域
    my @paWkLine=();     #文章加工の作業用領域
    my $pWkCnt;          #作業用カウンタ
    my $pWkTxt;          #編集用領域
    my $pI;              #添字
    my $pJ;              #添字
    my $pK;              #添字

    ### パラメータの受取 ###
    $pStatement=$_[0];

    ### 改行がある場合のみ処理を行う ###
    if (($pStatement =~ m/\n/s) eq $cgTRUE) {
        #=== 句点で分割 ===
        @paWkEdit = split(/。/,$pStatement);
        #== 句点と改行コードを復元 ===
        for ($pI=0; $pI<=$#paWkEdit; $pI++) {
            if ($pI eq $#paWkEdit) {
                #--- 分割の最後の要素の場合 ---
                if ($paWkEdit[$pI] eq '') {
                    #空の場合は要素を削除
                    pop @paWkEdit;
                }
            } else {
                #--- 分割の最後の要素以外の場合 ---
                #文末に句点を復元
                $paWkEdit[$pI]=join('',$paWkEdit[$pI],"。");
                #次行の先頭に改行コードがある場合は、２つまで元の行に復元する
                $pWkCnt=0;
                $pJ=$pI+1;
                while(($paWkEdit[$pJ] =~ m/^\n/s) eq $cgTRUE) {
                    $pWkCnt++;
                    if ($pWkCnt <= 2) {
                        $paWkEdit[$pI]=join('',$paWkEdit[$pI],"\n");
                    }
                    $paWkEdit[$pJ] =~ s/^\n//;
                }
            }
        }

        #=== 改行コード２つは別の文章とみなすため再編集 ===
        $paWkState=();
        $pI=-1;
        foreach $pWkTxt(@paWkEdit) {
            if (($pWkTxt =~ m/\n\n/s) eq $cgTRUE) {
                $pWkCnt=0;
                if (($pWkTxt =~ m/\n\n$/s) eq $cgTRUE) {
                    $pWkCnt=2;
                    chomp $pWkTxt;
                    chomp $pWkTxt;
                }

                @paWkEdit2=split(/\n\n/,$pWkTxt);
                for ($pJ=0; $pJ<$#paWkEdit2; $pJ++) {
                    $pI++;
                    $paWkState[$pI]=join('',$paWkEdit2[$pJ],"\n\n");
                }
                $pI++;
                if ($pWkCnt > 0) {
                    $paWkState[$pI]=join('',$paWkEdit2[$pJ],"\n\n");
                } else {
                    $paWkState[$pI]=$paWkEdit2[$pJ];
                }
            } else {
                $pI++;
                $paWkState[$pI]=$pWkTxt;
            }
        }
        @paWkEdit=();
        @paWkEdit2=();

        #=== 改行の編集 ===
        for ($pI=0; $pI<=$#paWkState; $pI++) {
            #--- 末尾の改行コードの編集 ---
            while(($paWkState[$pI] =~ m/\n$/s) == $cgTRUE) {
                $gaCSSStatement[$pI]=join('',$gaCSSStatement[$pI],'<br>');
                $paWkState[$pI] =~ s/\n$//;
            }
            #--- 文中に改行がある場合は、挿入位置を確認する ---
            if (($paWkState[$pI] =~ m/\n/s) eq $cgTRUE) {
                #改行位置と改行数の算出
                @paWkEdit=split(/\n/, $paWkState[$pI]);
                @paWkLine=();
                $pJ=-1;
                for ($pK=0; $pK<=$#paWkEdit; $pK++) {
                    if ($paWkEdit[$pK] ne '') {
                        $pJ++;
                        $paWkLine[$pJ][0]=$paWkEdit[$pK];
                        if ($pK == $#paWkEdit) {
                            $paWkLine[$pJ][1]=0;    #末尾の要素の場合は改行なし
                        } else {
                            $paWkLine[$pJ][1]=1;    #末尾の要素の場合は改行あり
                        }
                    } else {
                        $paWkLine[$pJ][1]++;    #改行数のカウント
                    }
                }

                for ($pK=0; $pK<=$pJ; $pK++) {
                    if ($paWkLine[$pK][1] == 0) {
                        $pBr='';
                    } elsif ($paWkLine[$pK][1] == 1) {
                        $pBr='<br>';
                    } else {
                        $pBr='<br><br>';
                    }

                    if ($pBr ne '') {
                        if (($gaCSSStatement[$pI] =~ m/$paWkLine[$pK][0]/s) eq $cgTRUE) {
                            #間にタグがない場合はそのまま置換
                            $pWkTxt=join('',$paWkLine[$pK][0],$pBr);
                            $gaCSSStatement[$pI] =~ s/$paWkLine[$pK][0]/$pWkTxt/xs;
                        } else {
                            #間にタグがある場合は、挿入処理を実施
                            $gaCSSStatement[$pI]=&subInsBr($gaCSSStatement[$pI],
                                                           $paWkLine[$pK][0],$pBr);
                        }
                    }
                }
            }
        }
    }

    # 変数のクリア
    @paWkState=();
    @paWkEdit=();
    @paWkEdit2=();
    @paWkLine=();

    return;
}

#************************************************************************
# SUB ROUTINE : CaboCha出力結果処理と本文のCSSタグ編集
#   引数１：JCorrect解析時の文番号
#   引数２：JCorrect解析時の文番号に対する文のCaboCha解析時の出力結果
#************************************************************************
sub subCaboCha($@) {
    ### 定数 ###
    my $cpEOS='EOS';          #CaboCha解析結果終端
    my $cpIdxKakarisaki=0;    #係り先文節番号(添字)
    my $cpIdxPhrase=10;       #文節(添字)

    ### 変数 ###
    my $pStatementNo;       #文番号(引数受取用)
    my @paCabocha=();       #CaboCha解析結果(引数受取用)
    my $pCaboCha;           #CaboCha解析結果行
    my @paWkCaboCha=();     #CaboCha解析結果再整理領域
    my $pIdxPhraseNo;       #文節数(添字)
    my $pPhrase;            #文節
    my @paConnection=();    #係り受け量過多集計領域
    my $pStartPos;          #開始位置
    my $pEndPos;            #終了位置
    my $pCnt;               #カウンタ
    my $pIndent;            #インデント用余白編集用
    my @paEditPhrase=();    #本文編集用
    my @paWkEdit=();        #編集作業領域
    my $pClass1;            #クラス編集用領域
    my $pClass2;            #クラス編集用領域
    my @paWkClass=();       #クラス編集作業領域
    my %phWkClass=();       #クラス編集作業領域
    my $pWkTxt;             #作業領域
    my $pI;                 #添字
    my $pJ;                 #添字
    my $pK;                 #添字
    my $pL;                 #添字

    ### 引数の受取 ###
    @paCaboCha=@_;
    $pStatementNo=shift(@paCaboCha);

    ### CaboCha出力結果の再整理 ###
    $pIdxPhraseNo=-1;
    foreach $pCaboCha(@paCaboCha) {
        chomp $pCaboCha;    #改行を除去

        #=== 終端記号で再整理終了 ===
        if ($pCaboCha eq $cpEOS) {
            last;
        }

        #=== 行を空白で分割する ===
        @paWkEdit=split(' ',$pCaboCha);
        if ($paWkEdit[0] eq '*') {
            #--- 文節の開始時は文節の係り先を編集 ---
            $pIdxPhraseNo++;
            #係り先番号
            chop $paWkEdit[2];
            $paWkCaboCha[$pIdxPhraseNo][$cpIdxKakarisaki]=$paWkEdit[2];
            #文節をクリア
            $paWkCaboCha[$pIdxPhraseNo][$cpIdxPhrase]='';
            #エラー種別ごとのエラー有無をクリア
            $paWkCaboCha[$pIdxPhraseNo][$cgERR_SUBJECT]=$cgFALSE;
            $paWkCaboCha[$pIdxPhraseNo][$cgERR_AVOID]=$cgFALSE;
            $paWkCaboCha[$pIdxPhraseNo][$cgERR_REVERSED]=$cgFALSE;
            $paWkCaboCha[$pIdxPhraseNo][$cgERR_PHRASE]=$cgFALSE;
            $paWkCaboCha[$pIdxPhraseNo][$cgERR_SENTENCE]=$cgFALSE;
            $paWkCaboCha[$pIdxPhraseNo][$cgERR_CONNECTION]=$cgFALSE;
            $paWkCaboCha[$pIdxPhraseNo][$cgERR_CHAIN]=$cgFALSE;
            #エラー種別ごとの部分エラー文言をクリア
            $paWkCaboCha[$pIdxPhraseNo][$cgERR_SUBJECT+10]='';
            $paWkCaboCha[$pIdxPhraseNo][$cgERR_AVOID+10]='';
            $paWkCaboCha[$pIdxPhraseNo][$cgERR_REVERSED+10]='';
            $paWkCaboCha[$pIdxPhraseNo][$cgERR_PHRASE+10]='';
            $paWkCaboCha[$pIdxPhraseNo][$cgERR_SENTENCE+10]='';
            $paWkCaboCha[$pIdxPhraseNo][$cgERR_CONNECTION+10]='';
            $paWkCaboCha[$pIdxPhraseNo][$cgERR_CHAIN+10]='';
        } elsif ($pIdxPhraseNo>=0) {
            #--- 文節の編集 ---
            $paWkCaboCha[$pIdxPhraseNo][$cpIdxPhrase]
                =join('',
                      $paWkCaboCha[$pIdxPhraseNo][$cpIdxPhrase],
                      $paWkEdit[0]);
        }
    }

    ### JCorrectのエラー文節をCaboChaの再整理結果に反映する ###
    for ($pI=1; $pI <= $gaErrorCnt[$pStatementNo]; $pI++) {
        if ($gaError[$pStatementNo][$pI][3] =~ m/\s/) {
            #=== 2文節の場合(REVERSEDエラーの場合のはず) ===
            @paWkEdit=split(' ',$gaError[$pStatementNo][$pI][3]);
            for ($pJ=0; $pJ<$pIdxPhraseNo; $pJ++) {
                if ($paWkCaboCha[$pJ][$cpIdxPhrase] eq $paWkEdit[0]) {
                    #--- 第１文節は完全一致 ---
                    $pK=$gaError[$pStatementNo][$pI][1];
                    $paWkCaboCha[$pJ][$pK]=$cgTRUE;
                    for ($pL=$pJ+1; $pL<=$pIdxPhraseNo; $pL++) {
                        if ($paWkCaboCha[$pL][$cpIdxPhrase] eq $paWkEdit[1]) {
                            #第２文節も完全一致
                            $pK=$gaError[$pStatementNo][$pI][1];
                            $paWkCaboCha[$pL][$pK]=$cgTRUE;
                            last;
                        } elsif ($paWkCaboCha[$pL][$cpIdxPhrase] =~ m/$paWkEdit[1]/) {
                            #第２文節は部分一致
                            $pK=$gaError[$pStatementNo][$pI][1];
                            $paWkCaboCha[$pL][$pK+10]=$paWkEdit[1];
                            last;
                        }
                    }
                } elsif ($paWkCaboCha[$pJ][$cpIdxPhrase] =~ m/$paWkEdit[0]$/) {
                    #--- 第１文節は部分一致 ---
                    $pK=$gaError[$pStatementNo][$pI][1];
                    $paWkCaboCha[$pJ][$pK+10]=$paWkEdit[0];
                    for ($pL=$pJ+1; $pL<=$pIdxPhraseNo; $pL++) {
                        if ($paWkCaboCha[$pL][$cpIdxPhrase] eq $paWkEdit[1]) {
                            #第２文節は完全一致
                            $pK=$gaError[$pStatementNo][$pI][1];
                            $paWkCaboCha[$pL][$pK]=$cgTRUE;
                            last;
                        } elsif ($paWkCaboCha[$pL][$cpIdxPhrase] =~ m/$paWkEdit[1]/) {
                            #第２文節も部分一致
                            $pK=$gaError[$pStatementNo][$pI][1];
                            $paWkCaboCha[$pL][$pK+10]=$paWkEdit[1];
                            last;
                        }
                    }
                }
            }
        } else {
            #=== 1文節の場合(SUBJECT/AVOIDエラーの場合のはず) ===
            $pWkTxt=$gaError[$pStatementNo][$pI][3];
            for ($pJ=0; $pJ<=$pIdxPhraseNo; $pJ++) {
                if ($paWkCaboCha[$pJ][$cpIdxPhrase] eq $pWkTxt) {
                    #--- 完全一致の場合 ---
                    $pK=$gaError[$pStatementNo][$pI][1];
                    $paWkCaboCha[$pJ][$pK]=$cgTRUE;
                } elsif ($paWkCaboCha[$pJ][$cpIdxPhrase] =~ m/$pWkTxt/) {
                    #--- 部分一致の場合 ---
                    $pK=$gaError[$pStatementNo][$pI][1];
                    $paWkCaboCha[$pJ][$pK+10]=$pWkTxt;
                }
            }
        } 
        @paWkEdit=();
    }

    ### 係り受け量過多チェック ###
    #=== 集計領域のクリア ===
    @paConnection=();
    for ($pI=0; $pI<=$pIdxPhraseNo; $pI++) {
        $paConnection[$pI]=0;
    }
    #=== 集中状況の集計 ===
    for ($pI=0; $pI<=$pIdxPhraseNo; $pI++) {
        $pJ=$paWkCaboCha[$pI][$cpIdxKakarisaki];
        if ($pJ >= 0) {
            $paConnection[$pJ]++;
        }
    }
    #=== 集中している場合はエラー ===
    for ($pI=0; $pI<=$pIdxPhraseNo; $pI++) {
        if ($paConnection[$pI] >= $cgBOUNDARY_CONNECTION) {
            #--- 係り先となっている文節をエラーとする ---
            @paWkEdit=();
            $pK=-1;
            for ($pJ=0; $pJ<=$pIdxPhraseNo; $pJ++) {
                if ($paWkCaboCha[$pJ][$cpIdxKakarisaki] eq $pI) {
                    $paWkCaboCha[$pJ][$cgERR_CONNECTION]=$cgTRUE;
                    $pK++;
                    $paWkEdit[$pK]=$paWkCaboCha[$pJ][$cpIdxPhrase];
                }
            }
            #--- 係り先の文節もエラーとする ---
            $paWkCaboCha[$pI][$cgERR_CONNECTION]=$cgTRUE;
            $pK++;
            $paWkEdit[$pK]=join('', $cgKWD_ARROW2,$paWkCaboCha[$pI][$cpIdxPhrase]);
            #--- 校正表示用にエラーを編集 ---
            # エラー件数をカウントアップ
            $pK=$gaErrorCnt[$pStatementNo]+1;
            $gaErrorCnt[$pStatementNo]=$pK;
            # 文番号を編集
            $gaError[$pStatementNo][$pK][0]=$pStatementNo+1;
            # エラー種別を編集
            $gaError[$pStatementNo][$pK][1]=$cgERR_CONNECTION;
            # エラー箇所(内容)を編集
            $gaError[$pStatementNo][$pK][2]=join("<br>",@paWkEdit);
            # エラー文節は編集不要のためクリア
            $gaError[$pStatementNo][$pK][3]='';
            #エラーありを編集
            $ghError{$cgERR_CONNECTION}=$cgTRUE;
        }
    }

    ### 係り受け冗長チェック ###
    $pStartPos=0;
    while($pStartPos<$pIdxPhraseNo) {
        #=== 係り受けの連続数のカウント ===
        $pCnt=1;
        for ($pI=$pStartPos+1; $pI<=$pIdxPhraseNo; $pI++) {
            $pEndPos=$pI;
            if (($paWkCaboCha[$pI-1][$cpIdxKakarisaki]+1)
                eq $paWkCaboCha[$pI][$cpIdxKakarisaki]) {
                #--- 係り先が連続している場合はカウントする ---
                $pCnt++;
            } else {
                #--- 係り先が連続していない場合はカウント終了 ---
                $pEndPos=$pI-1;   #終了位置に現在位置の１つ前を設定
                last;
            }
        }
        #=== 係り先の連続数が冗長している場合はエラー ===
        if ($pCnt >= $cgBOUNDARY_CHAINING) {
            #--- 開始位置から終了位置までをエラーとする ---
            @paWkEdit=();
            $pI=-1;
            $pIndent='';
            for ($pJ=$pStartPos; $pJ<=$pEndPos; $pJ++) {
                $paWkCaboCha[$pJ][$cgERR_CHAIN]=$cgTRUE;
                $pI++;
                $paWkEdit[$pI]=join('', $pIndent, $cgKWD_ARROW2, 
                                    $paWkCaboCha[$pJ][$cpIdxPhrase]);
                $pIndent=join('','　',$pIndent);
            }
            #--- 校正表示用にエラーを編集 ---
            # エラー件数をカウントアップ
            $pK=$gaErrorCnt[$pStatementNo]+1;
            $gaErrorCnt[$pStatementNo]=$pK;
            # 文番号を編集
            $gaError[$pStatementNo][$pK][0]=$pStatementNo+1;
            # エラー種別を編集
            $gaError[$pStatementNo][$pK][1]=$cgERR_CHAIN;
            # エラー箇所(内容)を編集
            $gaError[$pStatementNo][$pK][2]=join("<br>",@paWkEdit);
            # エラー文節は編集不要のためクリア
            $gaError[$pStatementNo][$pK][3]='';
            #エラーありを編集
            $ghError{$cgERR_CHAIN}=$cgTRUE;
        }
        #=== 終了位置の次へ開始位置を移動 ===
        $pStartPos=$pEndPos+1;
    }

    ### 本文の編集 ###
    for ($pI=0; $pI<=$pIdxPhraseNo; $pI++) {
        #=== 完全一致エラーのクラスの編集 ===
        $pClass1='';
        @paWkEdit=();
        @paWkClass=();
        %phWkClass=();
        $pJ=-1;
        foreach $pK($cgERR_SUBJECT,$cgERR_AVOID,$cgERR_REVERSED,
                    $cgERR_CONNECTION,$cgERR_CHAIN) {
            if ($paWkCaboCha[$pI][$pK] eq $cgTRUE) {
                #--- 完全一致エラーのクラスを集約する ---
                if ($pClass1 ne '') {
                    $pWkTxt=$pClass1;
                    $pClass1=join(' ',$pWkTxt,$ghClass{$pK});
                } else {
                    $pClass1=$ghClass{$pK};
                }
            } elsif ($paWkCaboCha[$pI][$pK+10] ne '') {
                #--- 部分一致エラーのクラスを集約する ---
                $pJ++;
                $paWkClass[$pJ]=$paWkCaboCha[$pI][$pK+10];
                if (defined($phWkClass{$paWkClass[$pJ]}) == $cgTRUE) {
                    $pWkTxt=$phWkClass{$paWkClass[$pJ]};
                    $phWkClass{$paWkClass[$pJ]}=join(' ',$pWkTxt,$ghClass{$pK});
                } else {
                    $phWkClass{$paWkClass[$pJ]}=$ghClass{$pK};
                }
            }
        }

        #=== 文節の書式設定 ===
        $pWkTxt=$paWkCaboCha[$pI][$cpIdxPhrase];
        #--- 完全一致エラーの編集 ---
        if ($pClass1 ne "") {
            $paEditPhrase[$pI]=join('', "<span class='",$pClass1,"'>",$pWkTxt,"</span>");
        } else {
            $paEditPhrase[$pI]=$pWkTxt;
        }
        #--- 部分一致エラーの編集 ---
        if ($pJ >= 0) {
            foreach $pPhrase(@paWkClass) {
                $pClass2=$phWkClass{$pPhrase};
                if ($pClass1 ne "") {
                    $pWkTxt=join('',"</span><span class='",$pClass2,"'>",
                                    $pPhrase,"</span><span class='",$pClass1,"'>");
                } else {
                    $pWkTxt=join('',"<span class='",$pClass2,"'>",$pPhrase,"</span>");
                }
                $paEditPhrase[$pI] =~ s/$pPhrase/$pWkTxt/g;
            }
        }
    }
    # 書式設定済の本文をグローバル変数に編集
    $gaCSSStatement[$pStatementNo]=join('',@paEditPhrase);

    # 変数のクリア
    @paCaboCha=();
    @paWkCaboCha=();
    @paConnection=();
    @paEditPhrase=();
    @paWkEdit=();
    @paWkClass=();
    %phWkClass=();

    return;
}

#************************************************************************
# SUB ROUTINE : キーワード文節取得
#   引数１：JCorrect解析時の警告行
#   引数２：エラー抽出キーワード１(必須)
#   引数３：エラー抽出キーワード２(任意)
#************************************************************************
sub subGetKeyword($$;$) {
    ### 変数 ###
    my $pWork1;
    my $pWork2;
    my $pPosStart;
    my $pPos1;
    my $pPos2;

    ### 検索開始位置を取得 ###
    $pPosStart=index $_[0], $_[1];
    $pPosStart=$pPosStart+length($_[1]);

    ### キーワード開始位置の検索 ###
    $pPos1=index $_[0], $cgKWD_START_WORD,$pPosStart;

    ### キーワード開始位置からの文字列の取得 ###
    $pWork1=substr($_[0], $pPos1+1);

    ### 終了位置の検索開始位置を取得 ###
    if (defined($_[2]) == 1) {
        $pPosStart=index $pWork1,$_[2];
    } else {
        $pPosStart=length($pWork1);
    }

    ### キーワード終了位置の検索 ###
    $pPos2=rindex $pWork1, $cgKWD_END_WORD,$pPosStart;

    ### キーワード終了位置までの文字列の取得 ###
    $pWork2=substr($pWork1, 0, $pPos2);

    return($pWork2);
}

#************************************************************************
# SUB ROUTINE : エラー上限桁数取得
#   引数１：JCorrect解析時の警告行
#   引数２：エラー抽出キーワード１(必須)
#   引数３：エラー抽出キーワード２(必須)
#************************************************************************
sub subGetErrMaxColumn($$$) {
    my $pWork1;
    my $pWork2;
    my $pPos1;
    my $pPos2;

    ### エラー上限桁数の前のキーワード終了位置を取得 ###
    $pPos1=index $_[0],$_[1];
    $pPos1=$pPos1 + length($_[1]);

    ### キーワード終了位置以降の値の取得 ###
    $pWork1=substr($_[0],$pPos1);
    $pWork1 =~ s/^\s+//;

    ### エラー上限桁数の後のキーワード開始位置を取得 ###
    $pPos2=index $pWork1,$_[2];

    ### キーワード開始位置より前の値の取得 ###
    $pWork2=substr($pWork1, 0 ,$pPos2);
    $pWork2 =~ s/\s+$//;

    return($pWork2);
}

#************************************************************************
# SUB ROUTINE : JCORRECTエラー情報処理
#   引数１：JCorrect解析時の警告行
#************************************************************************
sub subJCorrectError($) {
    ### 定数 ###
    my $cpERR_SUBJECT='misssing subject for ';    #主語なし
    my $cpERR_AVOID='avoid using ';               #冗長表現
    my $cpERR_REVERSED='reversed word order ';    #語順エラー
    my $cpERR_PHRASE='too long phrase ';          #文節長さ超過
    my $cpERR_SENTENCE='too long sentence ';      #１文長さ超過

    ### 変数 ###
    my $pStatementNo;    #文番号
    my $pErrorType;      #エラー種別
    my $pError;          #エラー箇所(内容)
    my $pPrase;          #エラー対象文節
    my $pWork1;          #作業領域
    my $pWork2;          #作業領域
    my @paWork;          #作業領域
    my $pI;              #添字(文番号-1)
    my $pJ;              #添字(エラー件数)

    ### 文番号の設定 ###
    $pStatementNo=$#gaStatement;
    $pStatementNo++;

    ### エラー種別、エラー箇所(内容),エラー対象文節のクリア ###
    $pErrorType="";
    $pError="";
    $pPhrase="";

    ### エラー種別ごとに処理を行う ###
    if ($_[0] =~ /$cpERR_SUBJECT/) {
        #=== 主語なしの場合 ===
        #エラー種別の編集
        $pErrorType=$cgERR_SUBJECT;
        #エラー箇所(内容)、エラー対象文節の編集
        $pWork1=&subGetKeyword($_[0],$cgKWD_SUBJECT);
        $pError=$pWork1;
        $pPhrase=$pWork1;

    } elsif ($_[0] =~ /$cpERR_AVOID/) {
        #=== 冗長表現の場合 ===
        #エラー種別の編集
        $pErrorType=$cgERR_AVOID;
        #エラー箇所(内容)、エラー対象文節の編集
        $pWork1=&subGetKeyword($_[0],$cgKWD_AVOID1,$cgKWD_AVOID2);
        $pWork2=&subGetKeyword($_[0],$cgKWD_AVOID2);
        $pError=join('',$pWork1,$cgKWD_ARROW,$pWork2);
        $pPhrase=$pWork1;

    } elsif ($_[0] =~ /$cpERR_REVERSED/) {
        #=== 語順エラーの場合 === 
        #エラー種別の編集
        $pErrorType=$cgERR_REVERSED;
        #エラー箇所(内容)、エラー対象文節の編集
        $pWork1=&subGetKeyword($_[0],$cgKED_REVERSED);
        @paWork=split(/$cgKWD_ARROW/,$pWork1);
        $pError=join('',$paWork[0],$paWork[1], $cgKWD_ARROW,$paWork[1],$paWork[0]);
        $pPhrase=join(' ',@paWork);
        @paWork=();

    } elsif ($_[0] =~ /$cpERR_PHRASE/) {
        #=== 文節長さ超過の場合 ===
        #エラー種別の編集
        $pErrorType=$cgERR_PHRASE;
        #エラー箇所(内容)の編集
        $pWork1=&subGetErrMaxColumn($_[0],$cgKWD_PHRASE1,$cgKWD_PHRASE2);
        $pError=join('',$cgMSG_PHRASE1,$pWork1,$cgMSG_PHRASE2);

    } elsif ($_[0] =~ /$cpERR_SENTENCE/) {
        #=== １文長さ超過の場合 ===
        #エラー種別の編集
        $pErrorType=$cgERR_SENTENCE;
        #エラー箇所(内容)の編集
        $pWork1=&subGetErrMaxColumn($_[0],$cgKWD_SENTENCE1,$cgKWD_SENTENCE2);
        $pError=join('',$cgMSG_SENTENCE1,$pWork1,$cgMSG_SENTENCE2);

    }

    ### エラー情報を保存 ###
    if ($pErrorType ne "") {
        $pI=$#gaStatement;                  #処理中の文のインデックスを取得
        $pJ=$gaErrorCnt[$pI];               #現在のエラー件数を取得
        $pJ++;                              #エラー件数のカウントアップ
        $gaErrorCnt[$pI]=$pJ;               #エラー件数を編集
        $gaError[$pI][$pJ][0]=$pI+1;        #文番号を編集
        $gaError[$pI][$pJ][1]=$pErrorType;  #エラー種別を編集
        $gaError[$pI][$pJ][2]=$pError;      #エラー箇所(内容)を編集
        $gaError[$pI][$pJ][3]=$pPhrase;     #対象文節を編集
        $ghError{$pErrorType}=$cgTRUE;      #エラーありを編集
    }

    #変数のクリア
    @paWork=();

    return;
}

#************************************************************************
# SUB ROUTINE : JCORRECT出力結果処理
#   引数１：JCorrect解析時の出力結果
#************************************************************************
sub subJCorrect(@) {
    ### 定数 ###
    my $cpSwStatement=1;    #文読み込み中
    my $cpSwTree=2;         #ツリー読み込み中
    my $cpSwError=3;        #エラー情報読み込み中

    ### 変数 ###
    my $pI;           #添字(JCORRECT出力結果参照用)
    my $pJ;           #添字(文章参照用)
    my $pK;           #添字(エラー情報参照用)
    my $pSw=0;        #読み込みスイッチ
    my $pLine;        #解析結果の行情報
    my $pStatement;   #文
    my $pWork;        #作業領域

    ### JCORRECT出力結果を読み込む ###
    $pSw=$cgFALSE;    #最初は初期値を設定
    $pStatement="";
    for ($pI=0; $pI<=$#_; $pI++) {
        #=== 行を取得 ===
        $pLine=$_[$pI];
        chomp $pLine;
        $pLine=~ s/^\s+//;

        if ($pLine eq "") {
            #=== 空行の出現でスイッチを切り替える ===
            if ($pSw == $cgFALSE) {
                $pSw=$cpSwStatement;
            } elsif ($pSw ==  $cpSwStatement) {
                $pSw=$cpSwTree;

            } elsif ($pSw == $cpSwTree) {
                $pSw=$cpSwError;
                
                $pJ=$#gaStatement;
                $pJ++;
                $gaStatement[$pJ]=$pStatement;    #文の保存
                $pStatement="";                   #作業領域をクリア
                $gaErrorCnt[$pJ]=0;               #文ごとのエラー件数をクリア

            } elsif ($pSw == $cpSwError) {
                $pSw=$cpSwStatement;
            }

        } else {
            #=== 文章の取得 ===
            if ($pSw ==  $cpSwStatement) {
                #文を取得する
                if ($pStatement eq "") {
                    $pStatement=$pLine;
                } else {
                    $pWork=join("",$pStatement,$pLine);
                    $pStatement=$pWork;
                }

            #=== ツリー情報は使用しない ===
            } elsif ($pSw == $cpSwTree) {
                #No Operation

            #=== エラー情報の取得 ===
            } else {
                # エラー取得処理
                &subJCorrectError($pLine);
            }
        }
    }

    return;
}

#************************************************************************
# MAIN ROUTINE
#************************************************************************
#========================================================================
# プライベート定数
#========================================================================
#-------
# FILES 
#-------
my $cpNKF='/usr/bin/nkf';
my $cpJCORRECT='/var/www/jcorrect-hs';
my $cpTMPFILE="/tmp/jcorrect$$";
my $cpCABOCHA='/usr/bin/cabocha';

#========================================================================
# CGIモジュールの使用
#========================================================================
use CGI;
use CGI::Carp qw(fatalsToBrowser);
$CGI::POST_MAX = 1024 * 1024;

my $pmdlCGI = new CGI;
$pmdlCGI->param;
die($pmdlCGI->cgi_error) if ($pmdlCGI->cgi_error);

#========================================================================
# 入力値の取得
#========================================================================
my $ptxtInput = $pmdlCGI->param('txtInput');
$ptxtInput =~ s/\r\n/\n/gsx;
$ptxtInput =~ s/\r/\n/gsx;
$gTopReturnCnt=0;
while (($ptxtInput =~ m/^\n/sx) eq $cgTRUE) {
    $gTopReturnCnt++;
    $ptxtInput =~ s/^\n//sx;
}

#========================================================================
# JCORRECT & CaboCha 解析
#========================================================================
my @paJCorrect=();
my @paCaboCha=();
if ($ptxtInput ne "") {
    #入力文字列の置換
    my $pStatement=$ptxtInput;
#    $pStatement =~ s/\.(\W)/。$1/g; 
#    $pStatement =~ s/\.$/。/g;
#    $pStatement =~ s/,\s?/、/g;
    $pStatement =~ s/\n{3,}/\n\n/g;
    $pStatement =~ s/\．(\W)/。$1/g; 
    $pStatement =~ s/\．$/。/g;
    $pStatement =~ s/，\s?/、/g;
    $pStatement =~ s/>/＞/g;
    $pStatement =~ s/</＜/g;
    $pStatement =~ s/\(/（/g;
    $pStatement =~ s/\)/）/g;
    $pStatement =~ s/\&/＆/g;
    $pStatement =~ s/\;/；/g;
    $pStatement =~ s/\'/’/g;
    $pStatement =~ s/\"/”/g;

    #環境変数の設定
    $ENV{'PATH'}="/usr/local/bin:" . $ENV{'PATH'};

    #TMPファイル出力
    open(TMP, ">$cpTMPFILE");
    print TMP $pStatement;
    close(TMP);

    #JCORRECT実行
    @paJCorrect=`$cpNKF -w $cpTMPFILE | $cpJCORRECT`;

    #TMPファイル削除
    unlink $cpTMPFILE;

    #JCORRECT実行結果の整理
    &subJCorrect(@paJCorrect);

    my $pLine;
    for ($pLine=0; $pLine<=$#gaStatement; $pLine++) {
        #CaboCha実行
        @paCaboCha=`echo $gaStatement[$pLine] | $cpCABOCHA -f1`;
        
        #CaboCha実行結果の整理
        &subCaboCha($pLine,@paCaboCha);
    }

    #改行の復元
    &subEditBR($pStatement);
}

# メモリ解放
@paJCorrect=();
@paCaboCha=();

#========================================================================
# 出力
#========================================================================
my $pPhrase;         #本文の書式変換対象文言
my $pClass;          #本文の書式
my $pWkTxt;          #文字列
my @paWkEdit=();     #文字列(編集用)
my $pI;              #添字
my $pJ;              #添字



# ヘッダ部;
print $pmdlCGI->header(-charset=>'utf-8');



print $pmdlCGI->start_html(
		-title=>'文章博士：Webベース文章校正支援装置(Monjo-Hakase: Web-based Automatic Text Correction Assistant for Technical Writing)',
		-charset=>'UTF-8', -encoding=>'UTF-8', -lang=>'ja-JP',
		-meta=>{'keywords'=>'文章校正,文章博士,校正支援,Webベース,技術文書,係り受け解析,フリー,CaboCha,jcorrect,Monjo-Hakase,Text correction Assistant,for Technical Writing','description'=>'係り受け解析にCaboChaを、語順・主語なし指摘等にjcorrectでの判定結果を用いた、フリーで利用可能な自動文章校正支援ツールです。可読性の高いレポート・論文・技術文書の校正支援を実現します。'},
		-style=>{'src'=>'njc.css'});

# FORM
print $pmdlCGI->start_form(-action=>$pmdlCGI->url);
print $pmdlCGI->start_div({-class=>container}),"\n";

# 見出し欄
print $pmdlCGI->start_div({-class=>header}),"\n";
#print $pmdlCGI->h1('文章博士（Monjo-Hakase）',{-class=>'title'}),"\n";
print "<h1 style='margin-bottom: 0px; height=10px;'>文章博士（Monjo-Hakase）</h1>\n";
print $pmdlCGI->p('技術文章・テクニカルライティング向け自動校正支援システム（Automatic Text Correcting Assistant for Technical Writing）'),"\n";
print $pmdlCGI->end_div,"\n";

# ガイド欄
print $pmdlCGI->start_div({-class=>sidebar1}),"\n";
print $pmdlCGI->start_ul({-class=>nav}),"\n";
$paWkEdit[0]='■添削結果の凡例■';
print $pmdlCGI->li($paWkEdit[0], $pmdlCGI->br, "\n",
                   $pmdlCGI->span({-class=>'error-missing-subject'},'文字'),
                   '：主語なし', $pmdlCGI->br, "\n",
                   $pmdlCGI->span({-class=>'error-avoid-using'},'文字'),
                   '：冗長表現', $pmdlCGI->br, "\n",
                   $pmdlCGI->span({-class=>'too-long-chaining'},'文字'),
                   '：係り受け長さ冗長', $pmdlCGI->br, "\n",
                   $pmdlCGI->span({-class=>'too-many-connection'},'文字'),
                   '：係り受け量過多', $pmdlCGI->br, "\n",
                   $pmdlCGI->span({-class=>'reversed-word-order'},'文字'),
                   '：語順エラー'),"\n";
@paWkEdit=();
#
$paWkEdit[0]='■使い方■';
$paWkEdit[1]='ページ左側のフォームに文章を入力し、校正または再校正ボタンを押すと、自動構成支援処理が開始され、結果が表示されます。';
$paWkEdit[2]='結果はフォームの下に表示されます。本文、校正結果、エラーについての説明が表示されますので、これを参考に文章を修正しましょう。';
print $pmdlCGI->li($paWkEdit[0], $pmdlCGI->br, "\n",
                   $paWkEdit[1], $pmdlCGI->br, "\n",
                   $pmdlCGI->br, "\n",
                   $paWkEdit[2]),"\n";
@paWkEdit=();
#
$paWkEdit[0]='■使用上の注意■';
$paWkEdit[1]='　本ソフトはjcorrect・CaboChaでの判定を利用し、自動処理によって文章を校正します。';
$paWkEdit[2]='　そのため、たまに係り受け解析を誤ることがあります。使用者自身が、新語・造語による係り受け誤処理を認識し、主語が曖昧でも主部が存在することを認識出来る場合は、エラーを無視して構いません。';
$paWkEdit[3]='　但し説明文では、文章の係り受けが機械的に出来る文書であるということは、「分かりやすい文」であることも意味します。この点に配慮・留意し、本ソフトをご利用ください。';
print $pmdlCGI->li($paWkEdit[0], $pmdlCGI->br, "\n",
                   $paWkEdit[1], $pmdlCGI->br, "\n",
                   $pmdlCGI->br, "\n",
                   $paWkEdit[2], $pmdlCGI->br, "\n",
                   $pmdlCGI->br, "\n",
                   $paWkEdit[3]),"\n";
@paWkEdit=();
print $pmdlCGI->end_ul,"\n";
print $pmdlCGI->end_div,"\n";

# 入力欄
print $pmdlCGI->start_div({-class=>content}),"\n";
print $pmdlCGI->h1('入力欄'),"\n";
print $pmdlCGI->start_table({-width=>"90%"},{-border=>"0"},
                            {-cellspacing=>"0"}),"\n";
#print $pmdlCGI->Tr($pmdlCGI->td(["&nbsp;"])),"\n";
$pWkTxt=$ptxtInput;
if ($gTopReturnCnt > 0) {
    for ($pI=0; $pI<=$gTopReturnCnt; $pI++) {
        $pWkTxt=join('',"\n",$pWkTxt);
    }
}
$paWkEdit[0]=join('',
             '<label for="txtInput">',
             '<textarea name="txtInput" rows="8" cols="90" style="width:100%;">',
             "$pWkTxt",'</textarea>','</label>',"\n");
$paWkEdit[1]=$pmdlCGI->br;
$paWkEdit[2]="\n";
if ($ptxtInput eq "") {
    $paWkEdit[3]=$pmdlCGI->submit(-name=>"btnKaiseki", -value=>"校正");
} else {
    $paWkEdit[3]=$pmdlCGI->submit(-name=>"btnKaiseki", -value=>"再校正");
}
print $pmdlCGI->start_Tr,"\n";
print $pmdlCGI->td({-class=>"width-95"},[join('',@paWkEdit)]),"\n";
print $pmdlCGI->end_Tr,"\n";
@paWkEdit=();
print $pmdlCGI->end_table,"\n";
print $pmdlCGI->end_div,"\n";
print $pmdlCGI->br, "\n";
print $pmdlCGI->br, "\n";
print $pmdlCGI->br, "\n";
print $pmdlCGI->br, "\n";

#本文欄
if ($ptxtInput ne "") {
    print $pmdlCGI->h1('本文'),"\n";
    print $pmdlCGI->start_table({-class=>"border0 width-70"}),"\n";
    print $pmdlCGI->start_Tr, "\n";
    print $pmdlCGI->td({-style=>"width: 15px;"},["&nbsp;"]),"\n";
    #print $pmdlCGI->start_p({-class=>"width-1"}),"\n";
    print $pmdlCGI->start_td, "\n";
    print join('',@gaCSSStatement);
    print "\n";
    print $pmdlCGI->end_td, "\n";
    print $pmdlCGI->end_Tr, "\n";
    print $pmdlCGI->end_table, "\n";
    #print $pmdlCGI->end_p,"\n";
    print $pmdlCGI->br, "\n";
    print $pmdlCGI->br, "\n";
}

#校正結果欄
if (($ghError{$cgERR_SUBJECT} == $cgTRUE)    ||
    ($ghError{$cgERR_AVOID} == $cgTRUE)      ||
    ($ghError{$cgERR_REVERSED} == $cgTRUE)   ||
    ($ghError{$cgERR_PHRASE} == $cgTRUE)     ||
    ($ghError{$cgERR_SENTENCE} == $cgTRUE)   ||
    ($ghError{$cgERR_CONNECTION} == $cgTRUE) ||
    ($ghError{$cgERR_CHAIN} == $cgTRUE)) {
    print $pmdlCGI->h1('校正結果'),"\n";
    print $pmdlCGI->start_table({-class=>"border0 width-70"}),"\n";
    print $pmdlCGI->start_Tr, "\n";
    print $pmdlCGI->td({-style=>"width: 15px;"},["&nbsp;"]),"\n";
    print $pmdlCGI->start_td,"\n";
    print $pmdlCGI->start_table({-class=>"border-collapse width-all"}),"\n";
    print $pmdlCGI->start_Tr, "\n";
    print $pmdlCGI->td({-class=>"tableheader border1 width-1"},
                       ["エラー内容"]), "\n";
    print $pmdlCGI->td({-class=>"tableheader border1 width-2"},
                       ["文番号"]), "\n";
    print $pmdlCGI->td({-class=>"tableheader border1"},
                       ["エラー箇所（矢印以降は推奨訂正例）"]), "\n";
    print $pmdlCGI->end_Tr,"\n";
    for ($pI=0; $pI<=$#gaStatement; $pI++) {
        for ($pJ=1;$pJ<=$gaErrorCnt[$pI]; $pJ++) {
            $paWkEdit[0]="border1";
            $paWkEdit[1]=$ghClass{$gaError[$pI][$pJ][1]};
            print $pmdlCGI->start_Tr,"\n";
            print $pmdlCGI->td({-class=>join(' ',@paWkEdit)},
                               [$cgaERR_TYPE[$gaError[$pI][$pJ][1]]]),"\n";
            print $pmdlCGI->td({-class=>"border1"},
                               $gaError[$pI][$pJ][0]),"\n";
            print $pmdlCGI->td({-class=>"border1"},
                               $gaError[$pI][$pJ][2]),"\n";
            print $pmdlCGI->end_Tr,"\n";
            #
            @paWkEdit=();
        }
    }
    print $pmdlCGI->end_table,"\n";
    print $pmdlCGI->end_td,"\n";
    print $pmdlCGI->end_Tr,"\n";
    print $pmdlCGI->end_table,"\n";
    print $pmdlCGI->br, "\n";
    print $pmdlCGI->br, "\n";

}

#エラーの解説欄
if (($ghError{$cgERR_SUBJECT} == $cgTRUE)  ||
    ($ghError{$cgERR_AVOID} == $cgTRUE)    ||
    ($ghError{$cgERR_REVERSED} == $cgTRUE) ||
    ($ghError{$cgERR_PHRASE} == $cgTRUE)   ||
    ($ghError{$cgERR_SENTENCE} == $cgTRUE) ||
    ($ghError{$cgERR_CHAIN} == $cgTRUE)) {
    print $pmdlCGI->h1('エラーの解説'),"\n";
}
if ($ghError{$cgERR_SUBJECT} == $cgTRUE) {    # 主語なしの解説
    print $pmdlCGI->dt($cgCMNT_SUBJECT_TITLE),"\n";
    foreach $pWkTxt(@cgaCMNT_SUBJECT) {
        print $pmdlCGI->dd($pWkTxt),"\n";
    }
}
if ($ghError{$cgERR_AVOID} == $cgTRUE) {    # 冗長表現の解説
    print $pmdlCGI->dt($cgCMNT_AVOID_TITLE),"\n";
    foreach $pWkTxt(@cgaCMNT_AVOID) {
        print $pmdlCGI->dd($pWkTxt),"\n";
    }
}
if ($ghError{$cgERR_REVERSED} == $cgTRUE) {    # 語順エラーの解説
    print $pmdlCGI->dt($cgCMNT_REVERSED_TITLE),"\n";
    foreach $pWkTxt(@cgaCMNT_REVERSED) {
        print $pmdlCGI->dd($pWkTxt),"\n";
    }
}
if ($ghError{$cgERR_PHRASE} == $cgTRUE) {    # 文節長さ超過の解説
    print $pmdlCGI->dt($cgCMNT_PHRASE_TITLE),"\n";
    foreach $pWkTxt(@cgaCMNT_PHRASE) {
        print $pmdlCGI->dd($pWkTxt),"\n";
    }
}
if ($ghError{$cgERR_SENTENCE} == $cgTRUE) {    # １文長さ超過の解説
    print $pmdlCGI->dt($cgCMNT_SENTENCE_TITLE),"\n";
    foreach $pWkTxt(@cgaCMNT_SENTENCE) {
        print $pmdlCGI->dd($pWkTxt),"\n";
    }
}
if ($ghError{$cgERR_CONNECTION} == $cgTRUE) {    # 係り受け量過多の解説
    print $pmdlCGI->dt($cgCMNT_CONNECTION_TITLE),"\n";
    foreach $pWkTxt(@cgaCMNT_CONNECTION) {
        print $pmdlCGI->dd($pWkTxt),"\n";
    }
}
if ($ghError{$cgERR_CHAIN} == $cgTRUE) {    # 係り受け長さ冗長の解説
    print $pmdlCGI->dt($cgCMNT_CHAIN_TITLE),"\n";
    foreach $pWkTxt(@cgaCMNT_CHAIN) {
        print $pmdlCGI->dd($pWkTxt),"\n";
    }
}
if (($ghError{$cgERR_SUBJECT} == $cgTRUE)    ||
    ($ghError{$cgERR_AVOID} == $cgTRUE)      ||
    ($ghError{$cgERR_REVERSED} == $cgTRUE)   ||
    ($ghError{$cgERR_PHRASE} == $cgTRUE)     ||
    ($ghError{$cgERR_SENTENCE} == $cgTRUE)   ||
    ($ghError{$cgERR_CONNECTION} == $cgTRUE) ||
    ($ghError{$cgERR_CHAIN} == $cgTRUE)) {
    print $pmdlCGI->end_dl,"\n";
}

print $pmdlCGI->br,"\n";

# 初回は改行を繰り返し表示を調整する
if ($ptxtInput eq "") {
    for ($pI=0; $pI<50; $pI++) {
        print $pmdlCGI->br,"\n";
    }
}

# フッター
print $pmdlCGI->start_div({-class=>"footer"}),"\n";
$paWkEdit[0]="Monjo-Hakaseは、jcorrect、CaboChaによる係り受け解析を利用した、Webベースで動作する技術文書向け文章校正補助システムです。";
print $pmdlCGI->p($paWkEdit[0]);
@paWkEdit=();
print $pmdlCGI->end_div,"\n";

#終端
print $pmdlCGI->end_div,"\n";
print $pmdlCGI->end_form,"\n";
print $pmdlCGI->end_html,"\n";

#========================================================================
# 終了処理
#========================================================================
@cgaERR_TYPE=();
@cgaCMNT_SUBJECT=();
@cgaCMNT_AVOID=();
@cgaCMNT_REVERSED=();
@cgaCMNT_PHRASE=();
@cgaCMNT_SENTENCE=();
@cgaCMNT_CONNECTION=();
@cgaCMNT_CHAIN=();
@gaStatement=();
@gaCSSStatement=();
@gaErrorCnt=();
@gaError=();
%ghError=();
%ghClass=();

#************************************************************************
# Monjo-Hakase PROGRAM END
#************************************************************************

