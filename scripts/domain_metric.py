"""Development TF-IDF contrast weights and minimum-cost weighted token alignment."""
from collections import Counter
import math
import re


def fit_weights(domain_docs, background_docs, series_by_meeting, boost_exclusions=()):
    """Document=meeting for AMI, original document for Brown; no evaluation inputs."""
    tf,df=Counter(),Counter()
    support={}
    for meeting,tokens in sorted(domain_docs.items()):
        tf.update(tokens)
        df.update(set(tokens))
        for token in set(tokens):
            support.setdefault(token,set()).add(series_by_meeting[meeting])
    bg=Counter()
    for tokens in background_docs:
        bg.update(set(tokens))
    nd,nb=len(domain_docs),len(background_docs)
    if not nd or not nb:
        raise ValueError('Both development and background documents are required')
    stats={}
    total_tokens=sum(tf.values())
    for token,count in sorted(tf.items()):
        if token in boost_exclusions or not re.fullmatch('[a-z]{3,}',token) or count<5 or df[token]<3 or len(support[token])<2:
            continue
        domain_idf=math.log((nd+1)/(df[token]+1))
        background_idf=math.log((nb+1)/(bg[token]+1))
        salience=(count/total_tokens)*max(0.0,background_idf-domain_idf)
        if salience>0:
            stats[token]=dict(count=count,meeting_df=df[token],series_count=len(support[token]),
                              background_df=bg[token],salience=salience)
    maximum=max((s['salience'] for s in stats.values()),default=0)
    weights={t:1+3*s['salience']/maximum for t,s in stats.items()} if maximum else {}
    return dict(weights=weights,statistics=stats,domain_documents=nd,background_documents=nb,
                domain_tokens=sum(tf.values()),domain_vocabulary_size=len(tf))


def weighted_distance(reference,hypothesis,weights):
    """Costs: D=w(ref), I=w(hyp), S=max(w(ref),w(hyp)); matches=0.

    Optimize weighted cost directly. Ties prefer match/substitution, deletion,
    insertion in that order. No compound merging. Return weighted components.
    """
    def weight(token):
        w=weights.get(token,1.0)
        if not math.isfinite(w) or w<=0:
            raise ValueError('Weights must be finite and positive')
        return w
    rw=[weight(t) for t in reference]
    hw=[weight(t) for t in hypothesis]
    # Cells: total, substitution cost, deletion cost, insertion cost.
    previous=[(0.,0.,0.,0.)]
    for w in hw:
        p=previous[-1]
        previous.append((p[0]+w,p[1],p[2],p[3]+w))
    for i,ref in enumerate(reference):
        p=previous[0]
        current=[(p[0]+rw[i],p[1],p[2]+rw[i],p[3])]
        for j,hyp in enumerate(hypothesis):
            p=previous[j]
            cost=0. if ref==hyp else max(rw[i],hw[j])
            substitution=(p[0]+cost,p[1]+cost,p[2],p[3])
            p=previous[j+1]
            deletion=(p[0]+rw[i],p[1],p[2]+rw[i],p[3])
            p=current[j]
            insertion=(p[0]+hw[j],p[1],p[2],p[3]+hw[j])
            current.append(min([substitution,deletion,insertion],key=lambda c:c[0]))
        previous=current
    total,sub,delete,insert=previous[-1]
    return dict(weighted_errors=total,substitution_cost=sub,deletion_cost=delete,
                insertion_cost=insert,reference_weight=sum(rw))
