import streamlit as st,pandas as pd,numpy as np,plotly.express as px,plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import *
f=st.session_state['global_filters']; d=filtered(deliveries(),f)
st.title('What is Pressure?')
a,b=st.columns(2)
with a: st.markdown('#### Batting · collapse and rescue'); st.markdown('<div class="note">Striker in slot 4–7; wickets lost ≥ 3 before over 12 or ≥ 4 before over 15; behind the rate (chase: RRR−CRR ≥ 1.5; batting first: at least 15 runs below par).</div>',unsafe_allow_html=True)
with b: st.markdown('#### Bowling · set batters hitting freely in the death'); st.markdown('<div class="note">Overs 16–20, wickets fallen ≤ 4, batting side scored ≥ 10 runs per over in the previous 12 legal balls.</div>',unsafe_allow_html=True)
comp=load_csv('pressure_vs_nonpressure.csv')
if f['competition']!='Both' and not comp.empty: comp=comp[comp.competition.eq(f['competition'])]
if comp.empty: empty('Pressure comparison table is unavailable.')
else:
    st.subheader('Pressure vs ordinary deliveries')
    st.caption('Metrics and units are taken from the precomputed analysis table; competition groups remain separate.')
    role=st.radio('Pressure type',['Batting','Bowling'],horizontal=True)
    cm=comp[comp.role.eq(role)].copy()
    metric_cols=[('run_rate_per_over','Runs per over','runs/over',1),('boundary_pct','Boundary %','percent of legal balls',100),
                 ('dot_pct','Dot-ball %','percent of legal balls',100),('wickets_per_100_balls','Wickets / 100 balls','wickets per 100 legal balls',1)]
    fig=make_subplots(rows=2,cols=2,subplot_titles=[m[1] for m in metric_cols],horizontal_spacing=.12,vertical_spacing=.2)
    for i,(col,title,unit,multiplier) in enumerate(metric_cols):
        row,colnum=divmod(i,2); row+=1; colnum+=1
        for state,color in [('Non-pressure',BLUE),('Pressure',PINK)]:
            part=cm[cm.pressure_group.eq(state)]
            fig.add_trace(go.Bar(x=part.competition,y=pd.to_numeric(part[col],errors='coerce')*multiplier,
                name=state,legendgroup=state,showlegend=(i==0),marker_color=color,
                hovertemplate='%{x}<br>'+state+': %{y:.2f} '+unit+'<extra></extra>'),row=row,col=colnum)
        fig.update_yaxes(title_text=unit,row=row,col=colnum)
        fig.update_xaxes(title_text='Competition',row=row,col=colnum)
    fig.update_layout(title=f'{role}: pressure vs ordinary deliveries',barmode='group')
    st.plotly_chart(plot_theme(fig,440),use_container_width=True)
wp=load_csv('win_probability_crosscheck.csv')
if f['competition']!='Both' and not wp.empty: wp=wp[wp.competition.eq(f['competition'])]
if not wp.empty:
    st.subheader('Win-probability-style cross-check')
    melted=wp.melt(id_vars='competition',value_vars=[c for c in wp.columns if c!='competition'],var_name='measure',value_name='win_rate')
    melted['measure']=melted.measure.str.replace('_win_proxy','',regex=False).str.replace('_',' ').str.replace('flagged','pressure').str.replace('unflagged','ordinary').str.replace('unpressure','ordinary')
    st.plotly_chart(plot_theme(px.bar(melted,x='competition',y='win_rate',color='measure',barmode='group',color_discrete_sequence=[PINK,BLUE,'#8f5aa8','#8c9aaa'],title='Historical match-outcome proxy for flagged vs ordinary deliveries',labels={'competition':'Competition','win_rate':'Observed win / defense proxy','measure':'State'})),use_container_width=True)
if not d.empty:
    t1,t2=st.tabs(['Where rule pressure occurs','Continuous score distribution'])
    with t1:
        heat=d.copy()
        heat['flag']=pressure_mask(heat,'bat',f).astype(float)
        heat['over_num']=pd.to_numeric(heat.overid,errors='coerce')
        heat['wicket_num']=pd.to_numeric(heat.wickets_before,errors='coerce')
        heat=heat[heat.over_num.between(1,20)&heat.wicket_num.between(0,10)]
        hm=heat.groupby(['over_num','wicket_num'],observed=True).flag.agg(['mean','size']).reset_index()
        if not hm.empty:
            grid=hm.pivot(index='wicket_num',columns='over_num',values='mean').reindex(index=range(0,11),columns=range(1,21))
            counts=hm.pivot(index='wicket_num',columns='over_num',values='size').reindex(index=range(0,11),columns=range(1,21)).fillna(0)
            fig=go.Figure(go.Heatmap(x=list(range(1,21)),y=list(range(0,11)),z=grid.to_numpy(),customdata=counts.to_numpy(),
                colorscale=[[0,'#F3F5FA'],[1,PINK]],zmin=0,zmax=1,connectgaps=False,colorbar=dict(title='Flag share',tickformat='.0%'),
                hovertemplate='Over %{x}<br>Wickets lost: %{y}<br>Flag share: %{z:.1%}<br>Deliveries: %{customdata:.0f}<extra></extra>'))
            fig.update_layout(title='Batting pressure share by over and wickets lost',height=430,
                xaxis=dict(title='Over',tickmode='array',tickvals=[1,4,7,10,13,16,20],range=[.5,20.5]),
                yaxis=dict(title='Wickets lost before ball',tickmode='linear',dtick=2,range=[-.5,10.5]))
            st.plotly_chart(plot_theme(fig,430),use_container_width=True)
        h2=d.dropna(subset=['rrr_crr_gap','balls_remaining']).copy()
        if not h2.empty:
            qlo,qhi=h2.rrr_crr_gap.quantile([.01,.99])
            h2=h2[h2.rrr_crr_gap.between(qlo,qhi)].copy()
            gap_edges=np.unique(np.quantile(h2.rrr_crr_gap,np.linspace(0,1,8)))
            ball_edges=np.array([0,20,40,60,80,100,120.0001])
            h2['gap_bin']=pd.cut(h2.rrr_crr_gap,gap_edges,include_lowest=True,duplicates='drop')
            h2['balls_bin']=pd.cut(h2.balls_remaining,ball_edges,include_lowest=True,duplicates='drop')
            h2['flag']=pressure_mask(h2,'bat',f).astype(float)
            hm2=h2.groupby(['gap_bin','balls_bin'],observed=True).flag.agg(['mean','size']).reset_index()
            if not hm2.empty:
                gaps=list(hm2.gap_bin.cat.categories); balls=list(hm2.balls_bin.cat.categories)
                gap_labels=[f'{v.left:.0f} to {v.right:.0f}' for v in gaps]
                ball_labels=[f'{v.left:.0f}–{min(v.right,120):.0f}' for v in balls]
                share=hm2.pivot(index='gap_bin',columns='balls_bin',values='mean').reindex(index=gaps,columns=balls)
                counts=hm2.pivot(index='gap_bin',columns='balls_bin',values='size').reindex(index=gaps,columns=balls).fillna(0)
                fig=go.Figure(go.Heatmap(x=ball_labels,y=gap_labels,z=share.to_numpy(),customdata=counts.to_numpy(),
                    colorscale=[[0,'#F3F5FA'],[1,PINK]],zmin=0,zmax=1,connectgaps=False,colorbar=dict(title='Flag share',tickformat='.0%'),
                    hovertemplate='Balls remaining: %{x}<br>RRR − CRR gap: %{y}<br>Flag share: %{z:.1%}<br>Deliveries: %{customdata:.0f}<extra></extra>'))
                fig.update_layout(title='Chase pressure share by required-rate gap and balls remaining',height=430,
                    xaxis=dict(title='Balls remaining',tickangle=-25),
                    yaxis=dict(title='RRR − CRR gap (runs/over)'))
                st.caption('Cells show the share of deliveries flagged for batting pressure. Hover a cell for the delivery count; the chase-gap bins use quantiles to keep the comparison readable.')
                st.plotly_chart(plot_theme(fig,430),use_container_width=True)
            else:
                empty('There are not enough chase-state observations to build this heatmap.')
        else:
            empty('Chase pressure states are unavailable for the selected filters.')
    with t2:
        dist=d.copy(); dist['score']=pd.to_numeric(dist.general_pressure_score,errors='coerce'); dist=dist.dropna(subset=['score'])
        if dist.empty: empty('Continuous pressure score is unavailable.')
        else:
            cut=dist.score.quantile(f['threshold']/100); dist['zone']=np.where(dist.score.ge(cut),'Flagged zone','Ordinary range')
            st.plotly_chart(plot_theme(px.histogram(dist,x='score',color='zone',nbins=30,barmode='overlay',opacity=.82,color_discrete_map={'Flagged zone':PINK,'Ordinary range':BLUE},title='General pressure score distribution · upper percentile highlighted',labels={'score':'General pressure score (0–1 percentile)','count':'Deliveries','zone':'Score range'})),use_container_width=True)
footer()
