import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import *

st.title('Reliability and Limits')
st.markdown('''<div class="note"><b>Limitations</b><br>Split-half rank stability is low (Spearman about 0.1). Several selected players have only 35–90 pressure balls. The analysis does not adjust for opposition strength or venue. Model C is a weak check for bowlers.</div>''',unsafe_allow_html=True)
st.caption('Intervals and inclusion percentages below are Model A match-bootstrap estimates. Model B final ordering has no separate bootstrap interval.')

tabs=st.tabs(['Batters','Bowlers'])
for tab,role in zip(tabs,['Batter','Bowler']):
    with tab:
        player=player_tables(role)
        final=load_csv('final_top10.csv')
        ids=set(final[final.role.eq(role)].player_id)
        q=player[player.player_id.isin(ids)].copy()
        if not q.empty and {'rating_ci_low','rating_ci_high','model_a_rating'}.issubset(q.columns):
            q['name_rank']=q['name']+' · Final '+q.model_b_rank.astype(int).astype(str)
            center=pd.to_numeric(q.model_a_rating,errors='coerce')
            fig=go.Figure(go.Scatter(x=center,y=q.name_rank,mode='markers',marker=dict(color=PINK,size=10),
                error_x=dict(type='data',symmetric=False,array=(pd.to_numeric(q.rating_ci_high,errors='coerce')-center).fillna(0),arrayminus=(center-pd.to_numeric(q.rating_ci_low,errors='coerce')).fillna(0)),
                customdata=q[['name','bootstrap_top10_pct','pressure_balls']].to_numpy(),
                hovertemplate='%{customdata[0]}<br>Model A rating %{x:.2f}<br>Top-10 inclusion %{customdata[1]}%<br>Pressure balls %{customdata[2]}<extra></extra>'))
            fig.update_layout(title=f'{role}: Model A rating with 95% bootstrap interval',xaxis_title='Model A rating (standardized units)',yaxis_title='Final-list player')
            st.plotly_chart(plot_theme(fig,420),use_container_width=True)
            inc=q.sort_values('model_b_rank')
            fig=px.bar(inc,x='name',y='bootstrap_top10_pct',color='bootstrap_top10_pct',color_continuous_scale=['#c9d4e5',PINK],title=f'{role}: bootstrap frequency in Model A top 10',labels={'name':'Final-list player','bootstrap_top10_pct':'Bootstrap top-10 inclusion (%)'})
            st.plotly_chart(plot_theme(fig,320),use_container_width=True)
        else:
            empty(f'{role} bootstrap estimates are n/a in the supplied files.')

        half_summary=load_csv('split_half_reliability.csv')
        half_summary=half_summary[half_summary.role.eq(role)] if not half_summary.empty and 'role' in half_summary else pd.DataFrame()
        half_players=load_csv('split_half_players.csv')
        half_players=half_players[half_players.role.eq(role)] if not half_players.empty and 'role' in half_players else pd.DataFrame()
        if not half_players.empty:
            rho=pd.to_numeric(half_summary.spearman_rank_correlation,errors='coerce').iloc[0] if not half_summary.empty else float('nan')
            fig=px.scatter(half_players,x='odd_impact_per_ball',y='even_impact_per_ball',hover_name='name',hover_data=['odd_rank','even_rank'],title=f'{role}: odd- vs even-match pressure impact · Spearman rank correlation {display_number(rho,3)}',labels={'odd_impact_per_ball':'Odd-match impact (runs/ball)','even_impact_per_ball':'Even-match impact (runs/ball)','odd_rank':'Odd rank','even_rank':'Even rank'})
            lo=min(half_players.odd_impact_per_ball.min(),half_players.even_impact_per_ball.min()); hi=max(half_players.odd_impact_per_ball.max(),half_players.even_impact_per_ball.max())
            fig.add_shape(type='line',x0=lo,y0=lo,x1=hi,y1=hi,line=dict(color='#68748a',dash='dash'))
            st.plotly_chart(plot_theme(fig,420),use_container_width=True)
        else:
            st.info('Odd/even player-level ranks are n/a: the supplied split-half summary has only the aggregate Spearman value, and player-level rows could not be recovered from the analysis outputs.')
        if not half_summary.empty: st.dataframe(half_summary,hide_index=True,use_container_width=True)

        season=load_csv('season_top10_stability.csv')
        if not season.empty and 'role' in season:
            st.subheader('Adjacent-season overlap')
            st.dataframe(season[season.role.eq(role)],hide_index=True,use_container_width=True)
        else: st.info('Adjacent-season overlap: n/a in the supplied files.')

        sensitivity=load_csv('sensitivity_analysis.csv')
        if not sensitivity.empty and 'role' in sensitivity:
            st.subheader('Threshold and weight sensitivity')
            st.dataframe(sensitivity[sensitivity.role.eq(role)],hide_index=True,use_container_width=True)
        else: st.info('Threshold sensitivity: n/a in the supplied files.')
footer()
