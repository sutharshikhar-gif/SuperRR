from pathlib import Path
import json
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).parent
DATA = ROOT / 'data'
NAVY, PINK, BG, BLUE, GREEN, RED = '#0B1F4B', '#E5007D', '#F3F5FA', '#4E79A7', '#2E8B57', '#C84C5A'

@st.cache_data(show_spinner=False)
def load_csv(name):
    p = DATA / name
    return pd.read_csv(p, low_memory=False) if p.exists() else pd.DataFrame()

@st.cache_resource(show_spinner='Loading delivery detail…')
def deliveries():
    p = DATA / 'deliveries.parquet'
    if p.exists(): return pd.read_parquet(p)
    return pd.read_csv(DATA / 'deliveries.csv.gz', low_memory=False)

@st.cache_resource
def _filtered_frame_cache():
    return {}

def plot_theme(fig, height=360):
    fig.update_layout(template='plotly_white', height=height, margin=dict(l=12,r=12,t=58,b=12),
                      font=dict(family='Inter, system-ui, sans-serif', color=NAVY),
                      title_font=dict(size=18, color=NAVY), paper_bgcolor='white', plot_bgcolor='white',
                      legend_title_text='')
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor='#E8ECF4')
    return fig

def footer():
    n=deliveries().match_id.nunique()
    audit_path=DATA/'source_audit.json'
    raw_n=json.loads(audit_path.read_text()).get('raw_matches_with_ball_data') if audit_path.exists() else None
    reconciliation=f' · PDF raw-source count {raw_n:,} includes 30 non-IPL T20 matches outside this analysis scope' if raw_n and raw_n!=n else ''
    st.markdown(f'<div class="foot">Data window: IPL + T20I, 2022 onwards · {n:,} analysis matches included{reconciliation} · Rankings are best-evidence estimates; see Reliability and Limits</div>', unsafe_allow_html=True)

def season_year(series):
    return pd.to_numeric(series.astype(str).str.extract(r'(\d{4})',expand=False),errors='coerce')

def sidebar():
    st.sidebar.markdown('### Explore the evidence')
    comp = st.sidebar.selectbox('Competition', ['Both','IPL','T20I'])
    full = deliveries()
    years = sorted(pd.to_numeric(full.get('season_year', season_year(full.season)), errors='coerce').dropna().astype(int).unique().tolist())
    yr = st.sidebar.select_slider('Season range', options=years, value=(min(years),max(years))) if years else (2022,2026)
    min_bat = st.sidebar.slider('Minimum batter pressure balls',0,200,50,5)
    min_bowl = st.sidebar.slider('Minimum bowler pressure balls',0,200,30,5)
    mode = st.sidebar.radio('Pressure view',['Rule flag','Continuous score'])
    threshold = st.sidebar.slider('Continuous score percentile',50,99,75) if mode == 'Continuous score' else 75
    st.sidebar.caption('Competition and season filters apply to delivery and match views. Saved ranking metrics keep their analysis-period values.')
    return {'competition':comp,'years':yr,'min_bat':min_bat,'min_bowl':min_bowl,'mode':mode,'threshold':threshold}

def filtered(d, f):
    if d.empty: return d
    comp=f.get('competition','Both'); years=tuple(f.get('years',()))
    has_comp=comp!='Both' and 'competition' in d
    year_col='season_year' if 'season_year' in d else ('season' if 'season' in d else None)
    has_year=year_col is not None and len(years)==2
    if not has_comp and not has_year: return d
    key=(id(d),comp,years if has_year else None)
    cache=_filtered_frame_cache()
    if key in cache: return cache[key]
    mask=pd.Series(True,index=d.index)
    if has_comp: mask &= d.competition.eq(comp)
    if has_year:
        y=pd.to_numeric(d[year_col],errors='coerce') if year_col=='season_year' else season_year(d[year_col])
        mask &= y.between(*years)
    if len(cache)>12: cache.clear()
    cache[key]=d.loc[mask]
    return cache[key]

def pressure_mask(d, role, f):
    c='bat_pressure_flag' if role=='bat' else 'bowl_pressure_flag'
    s='bat_pressure_score' if role=='bat' else 'bowl_pressure_score'
    if f['mode']=='Rule flag' or s not in d: return d[c].fillna(False).astype(bool)
    valid=pd.to_numeric(d[s],errors='coerce')
    cut=valid.quantile(f['threshold']/100) if valid.notna().any() else np.inf
    return valid.ge(cut)

def metric_card(label,value,sub=''):
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-sub">{sub}</div></div>',unsafe_allow_html=True)

def empty(msg='No rows match these filters. Try widening the season or competition selection.'):
    st.info(msg)

def player_tables(role):
    return load_csv('player_batting.csv' if role=='Batter' else 'player_bowling.csv')

def leaderboard(role, model, f):
    final=load_csv('final_top10.csv'); x=player_tables(role)
    x=filtered(x,f)
    rankcol={'Model A':'model_a_rank','Model B':'model_b_rank','Model C':'model_c_rank'}[model]
    if model=='Model B':
        order=final[final.role==role][['rank','player_id','name']].copy(); order=order.rename(columns={'rank':'rank'})
        out=order.merge(x,on=['player_id','name'],how='left'); out['rank']=out['rank'].astype(int)
    elif model=='Model A':
        out=x[x.model_a_rank.notna()].copy(); out['rank']=pd.to_numeric(out.model_a_rank).astype(int); out=out.nsmallest(10,'rank')
    else:
        out=final[final.role==role][['rank','player_id','name']].merge(x,on=['player_id','name'],how='left')
        out['rank']=pd.to_numeric(out.model_c_rank,errors='coerce')
        out=out.sort_values(['rank','name'],na_position='last')
    return out.sort_values('rank')

def team_display(row):
    franchise=str(row.get('ipl_franchises','') or '').strip()
    nation=str(row.get('national_sides','') or '').strip()
    parts=[]
    if franchise: parts.append(f"IPL: {franchise}")
    if nation: parts.append(f"National: {nation}")
    return ' · '.join(parts) if parts else 'n/a'

def display_number(value, digits=2, suffix=''):
    try:
        return f"{float(value):.{digits}f}{suffix}" if pd.notna(value) else 'n/a'
    except (TypeError, ValueError):
        return 'n/a'

def metric_comparison_grid(metrics, title):
    """Plot each differently scaled pressure/baseline measure on its own y-axis."""
    fig=make_subplots(rows=2,cols=2,subplot_titles=[m[0] for m in metrics],horizontal_spacing=.12,vertical_spacing=.2)
    for i,(label,pressure,baseline,unit,multiplier) in enumerate(metrics):
        row,col=divmod(i,2); row+=1; col+=1
        for state,value,color in [('Pressure',pressure,PINK),('Baseline',baseline,BLUE)]:
            shown=pd.to_numeric(pd.Series([value]),errors='coerce').iloc[0]
            y=[float(shown)*multiplier] if pd.notna(shown) else [None]
            fig.add_trace(go.Bar(x=[state],y=y,name=state,legendgroup=state,showlegend=(i==0),marker_color=color,
                hovertemplate=state+': %{y:.2f} '+unit+'<extra></extra>'),row=row,col=col)
        fig.update_yaxes(title_text=unit,row=row,col=col)
        fig.update_xaxes(title_text='',row=row,col=col)
    fig.update_layout(title=title,barmode='group')
    return plot_theme(fig,500)

def add_player_link(role, player_id):
    st.session_state['selected_batter_id' if role=='Batter' else 'selected_bowler_id']=int(player_id)
    st.switch_page('pages/04_Batter_Deep_Dive.py' if role=='Batter' else 'pages/05_Bowler_Deep_Dive.py')
