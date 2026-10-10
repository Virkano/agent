<template>
  <div class="recommendation-page" v-loading="pageLoading">
    <header class="hero">
      <div>
        <span class="eyebrow">RECOMMENDATION / X05</span>
        <h2>召回与精排推荐引擎</h2>
        <p>完成双塔召回、多路融合、可解释精排、反馈增量与版本效果监控的推荐闭环。</p>
      </div>
      <div class="hero-actions">
        <el-button :icon="Refresh" @click="loadDashboard">刷新</el-button>
        <el-button :icon="Setting" @click="openRankingConfig">精排策略</el-button>
        <el-button :icon="Setting" @click="openFusionConfig">融合配置</el-button>
        <el-button :icon="Files" :loading="snapshotLoading" @click="createSnapshot">生成特征快照</el-button>
        <el-button type="primary" :icon="Cpu" @click="openTrainDialog">启动训练</el-button>
      </div>
    </header>

    <section class="summary-grid">
      <article>
        <span>用户特征</span>
        <strong>{{ dashboard.summary.user_feature_count }}</strong>
        <small>快照 v{{ dashboard.summary.snapshot_version || '—' }}</small>
      </article>
      <article>
        <span>物料特征</span>
        <strong>{{ dashboard.summary.item_feature_count }}</strong>
        <small>来源于已上线营销活动</small>
      </article>
      <article>
        <span>成功训练</span>
        <strong>{{ dashboard.summary.successful_run_count }}</strong>
        <small>共 {{ dashboard.summary.model_version_count }} 个模型版本</small>
      </article>
      <article class="published-card">
        <span>当前发布版本</span>
        <strong>{{ dashboard.summary.published_version ? `v${dashboard.summary.published_version}` : '—' }}</strong>
        <small>累计 {{ dashboard.summary.inference_count }} 次在线推理</small>
      </article>
      <article class="fusion-card">
        <span>融合召回</span>
        <strong>{{ fusionDashboard.summary.fusion_run_count }}</strong>
        <small>{{ fusionDashboard.summary.active_channel_count }} 路已启用 · 最近 {{ fusionDashboard.summary.latest_latency_ms ?? '—' }} ms</small>
      </article>
      <article class="ranking-card">
        <span>精排运行</span>
        <strong>{{ rankingDashboard.summary.ranking_run_count }}</strong>
        <small>策略 v{{ rankingDashboard.summary.published_version || '—' }} · 最近 {{ rankingDashboard.summary.latest_latency_ms ?? '—' }} ms</small>
      </article>
      <article class="incremental-card">
        <span>有效反馈样本</span>
        <strong>{{ incrementalDashboard.summary.labeled_sample_count }}</strong>
        <small>正向 {{ incrementalDashboard.summary.positive_count }} · 负向 {{ incrementalDashboard.summary.negative_count }}</small>
      </article>
      <article class="effect-card">
        <span>{{ effectDashboard.period.days }}日 CTR / CVR</span>
        <strong>{{ formatScore(effectDashboard.summary.ctr) }} / {{ formatScore(effectDashboard.summary.cvr) }}</strong>
        <small>覆盖 {{ formatScore(effectDashboard.summary.coverage_rate) }} · P95 {{ effectDashboard.latency.p95_total_ms }} ms</small>
      </article>
    </section>

    <el-alert
      title="当前已形成双塔召回 → 多路融合 → TopN 精排 → 反馈增量 → 版本效果监控闭环；所有指标均来自可追溯运行与反馈事件。"
      type="info"
      :closable="false"
      show-icon
      class="baseline-note"
    />

    <el-card shadow="never" class="workbench">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="精排 TopN" name="ranking">
          <div class="inference-layout">
            <aside class="inference-form">
              <div class="section-heading">
                <strong>二阶段精排测试</strong>
                <span>先生成多路候选集，再用当前已发布精排策略输出 TopN。</span>
              </div>
              <el-form label-position="top">
                <el-form-item label="营销客户">
                  <el-select v-model="rankingForm.customer_id" filterable placeholder="请选择客户" no-data-text="暂无营销客户">
                    <el-option
                      v-for="customer in dashboard.customers"
                      :key="customer.id"
                      :value="customer.id"
                      :label="`${customer.name} · ${customer.province || '未知地区'} · ${customer.current_plan || '未知套餐'}`"
                    />
                  </el-select>
                </el-form-item>
                <div class="form-grid compact-grid">
                  <el-form-item label="输出数量 TopN">
                    <el-input-number v-model="rankingForm.top_n" :min="1" :max="50" />
                  </el-form-item>
                  <el-form-item label="候选池大小">
                    <el-input-number v-model="rankingForm.candidate_pool_size" :min="5" :max="100" />
                  </el-form-item>
                </div>
                <div class="channel-preview">
                  <span>当前精排策略</span>
                  <strong>v{{ rankingDashboard.summary.published_version || '—' }}</strong>
                </div>
                <el-button
                  type="primary"
                  :icon="Search"
                  :loading="rankingLoading"
                  :disabled="!rankingForm.customer_id || !rankingDashboard.summary.published_version"
                  @click="runRankingInference"
                >
                  执行候选精排
                </el-button>
              </el-form>
            </aside>

            <section class="inference-result">
              <div v-if="rankingResult" class="result-meta">
                <div><span>精排策略</span><strong>v{{ rankingResult.ranking_version }}</strong></div>
                <div><span>候选 → TopN</span><strong>{{ rankingResult.candidate_count }} → {{ rankingResult.candidates.length }}</strong></div>
                <div><span>召回 / 精排耗时</span><strong>{{ rankingResult.fusion_latency_ms }} / {{ rankingResult.ranking_latency_ms }} ms</strong></div>
                <div><span>推荐客户</span><strong>{{ rankingResult.customer.name }}</strong></div>
              </div>
              <el-table v-if="rankingResult?.candidates.length" :data="rankingResult.candidates" stripe>
                <el-table-column prop="rank" label="#" width="54" />
                <el-table-column label="推荐物料" min-width="210">
                  <template #default="{ row }">
                    <div class="primary-cell"><strong>{{ row.campaign_name }}</strong><span>{{ row.campaign_code }} · {{ row.benefit }}</span></div>
                  </template>
                </el-table-column>
                <el-table-column label="精排 / 召回分" width="145">
                  <template #default="{ row }">
                    <div class="primary-cell"><strong class="score">{{ formatScore(row.rank_score) }}</strong><span>{{ formatScore(row.recall_score) }}</span></div>
                  </template>
                </el-table-column>
                <el-table-column label="可解释特征贡献" min-width="340">
                  <template #default="{ row }">
                    <el-popover
                      v-for="feature in row.feature_details"
                      :key="feature.feature"
                      placement="top"
                      :width="310"
                      trigger="hover"
                    >
                      <template #reference>
                        <el-tag size="small" effect="plain">{{ feature.label }} +{{ formatScore(feature.contribution) }}</el-tag>
                      </template>
                      <div class="source-detail">
                        <strong>{{ feature.label }}</strong>
                        <span>特征值 {{ formatScore(feature.value) }} × 权重 {{ formatWeight(feature.weight) }}</span>
                        <p>{{ feature.reason }}</p>
                      </div>
                    </el-popover>
                  </template>
                </el-table-column>
                <el-table-column label="反馈" width="170" fixed="right">
                  <template #default="{ row }">
                    <el-button link type="primary" @click="recordFeedback(row.campaign_id, 'CLICKED')">点击</el-button>
                    <el-button link type="success" @click="recordFeedback(row.campaign_id, 'CONVERTED')">转化</el-button>
                    <el-button link type="danger" @click="recordFeedback(row.campaign_id, 'NEGATIVE')">负反馈</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-else description="请选择客户并执行候选精排" />
            </section>
          </div>
        </el-tab-pane>

        <el-tab-pane label="多路融合" name="fusion">
          <div class="inference-layout">
            <aside class="inference-form">
              <div class="section-heading">
                <strong>融合召回测试</strong>
                <span>同一物料跨通道去重，并保留每个来源的分数、权重与解释。</span>
              </div>
              <el-form label-position="top">
                <el-form-item label="营销客户">
                  <el-select v-model="fusionForm.customer_id" filterable placeholder="请选择客户" no-data-text="暂无营销客户">
                    <el-option
                      v-for="customer in dashboard.customers"
                      :key="customer.id"
                      :value="customer.id"
                      :label="`${customer.name} · ${customer.province || '未知地区'} · ${customer.current_plan || '未知套餐'}`"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="召回数量 TopK">
                  <el-input-number v-model="fusionForm.top_k" :min="1" :max="50" />
                </el-form-item>
                <div class="channel-preview">
                  <span>当前启用</span>
                  <div>
                    <el-tag v-for="channel in enabledChannelOptions" :key="channel.value" size="small" effect="plain">
                      {{ channel.label }} {{ formatWeight(fusionConfig.weights[channel.value]) }}
                    </el-tag>
                  </div>
                </div>
                <el-button
                  type="primary"
                  :icon="Connection"
                  :loading="fusionLoading"
                  :disabled="!fusionForm.customer_id"
                  @click="runFusionInference"
                >
                  执行多路融合
                </el-button>
              </el-form>
            </aside>

            <section class="inference-result">
              <div v-if="fusionResult" class="result-meta">
                <div><span>模型版本</span><strong>{{ fusionResult.model_version ? `v${fusionResult.model_version}` : '未启用' }}</strong></div>
                <div><span>融合耗时</span><strong>{{ fusionResult.latency_ms }} ms</strong></div>
                <div><span>召回客户</span><strong>{{ fusionResult.customer.name }}</strong></div>
              </div>
              <el-table v-if="fusionResult?.candidates.length" :data="fusionResult.candidates" stripe>
                <el-table-column type="index" label="#" width="54" />
                <el-table-column label="推荐物料" min-width="210">
                  <template #default="{ row }">
                    <div class="primary-cell"><strong>{{ row.campaign_name }}</strong><span>{{ row.campaign_code }} · {{ row.benefit }}</span></div>
                  </template>
                </el-table-column>
                <el-table-column label="融合分数" width="112">
                  <template #default="{ row }"><strong class="score">{{ formatScore(row.score) }}</strong></template>
                </el-table-column>
                <el-table-column label="召回来源与贡献" min-width="300">
                  <template #default="{ row }">
                    <el-popover
                      v-for="source in row.source_details"
                      :key="source.channel"
                      placement="top"
                      :width="290"
                      trigger="hover"
                    >
                      <template #reference>
                        <el-tag size="small" effect="plain">{{ source.channel_label }} +{{ formatScore(source.contribution) }}</el-tag>
                      </template>
                      <div class="source-detail">
                        <strong>{{ source.channel_label }}</strong>
                        <span>通道分 {{ formatScore(source.score) }} × 权重 {{ formatWeight(source.weight) }}</span>
                        <p>{{ source.reason }}</p>
                      </div>
                    </el-popover>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-else description="请选择客户并执行多路融合召回" />
            </section>
          </div>
        </el-tab-pane>

        <el-tab-pane label="TopK 推理" name="inference">
          <div class="inference-layout">
            <aside class="inference-form">
              <div class="section-heading">
                <strong>在线召回测试</strong>
                <span>选择客户，使用当前已发布模型计算用户向量并检索物料向量。</span>
              </div>
              <el-form label-position="top">
                <el-form-item label="营销客户">
                  <el-select
                    v-model="inferenceForm.customer_id"
                    filterable
                    placeholder="请选择客户"
                    no-data-text="暂无营销客户"
                  >
                    <el-option
                      v-for="customer in dashboard.customers"
                      :key="customer.id"
                      :value="customer.id"
                      :label="`${customer.name} · ${customer.province || '未知地区'} · ${customer.current_plan || '未知套餐'}`"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="召回数量 TopK">
                  <el-input-number v-model="inferenceForm.top_k" :min="1" :max="50" />
                </el-form-item>
                <el-button
                  type="primary"
                  :icon="Search"
                  :loading="inferenceLoading"
                  :disabled="!inferenceForm.customer_id || !dashboard.summary.published_version"
                  @click="runInference"
                >
                  执行双塔召回
                </el-button>
              </el-form>
            </aside>

            <section class="inference-result">
              <div v-if="inferenceResult" class="result-meta">
                <div><span>模型版本</span><strong>v{{ inferenceResult.model_version }}</strong></div>
                <div><span>推理耗时</span><strong>{{ inferenceResult.latency_ms }} ms</strong></div>
                <div><span>召回客户</span><strong>{{ inferenceResult.customer.name }}</strong></div>
              </div>
              <el-table v-if="inferenceResult?.candidates.length" :data="inferenceResult.candidates" stripe>
                <el-table-column type="index" label="#" width="54" />
                <el-table-column label="推荐物料" min-width="220">
                  <template #default="{ row }">
                    <div class="primary-cell">
                      <strong>{{ row.campaign_name }}</strong>
                      <span>{{ row.campaign_code }} · {{ row.benefit }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="模型分数" width="120">
                  <template #default="{ row }"><strong class="score">{{ formatScore(row.score) }}</strong></template>
                </el-table-column>
                <el-table-column label="可解释特征" min-width="230">
                  <template #default="{ row }">
                    <el-tag v-for="reason in row.reasons" :key="reason" size="small" effect="plain">{{ reason }}</el-tag>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty
                v-else
                :description="dashboard.summary.published_version ? '请选择客户并执行召回' : '请先生成快照并训练发布模型'"
              />
            </section>
          </div>
        </el-tab-pane>

        <el-tab-pane label="效果监控" name="effect">
          <div class="effect-toolbar">
            <div class="section-heading">
              <strong>推荐效果与版本表现</strong>
              <span>统一观察曝光漏斗、目录覆盖、列表多样性、端到端延迟和各精排版本表现。</span>
            </div>
            <el-select v-model="effectPeriod" class="period-select" @change="loadEffectDashboard">
              <el-option label="最近 7 天" :value="7" />
              <el-option label="最近 30 天" :value="30" />
              <el-option label="最近 90 天" :value="90" />
            </el-select>
          </div>
          <div class="effect-grid" v-loading="effectLoading">
            <article><span>点击率 CTR</span><strong>{{ formatScore(effectDashboard.summary.ctr) }}</strong><small>{{ effectDashboard.summary.click_count }} / {{ effectDashboard.summary.exposure_count }} 次</small></article>
            <article><span>转化率 CVR</span><strong>{{ formatScore(effectDashboard.summary.cvr) }}</strong><small>{{ effectDashboard.summary.conversion_count }} / {{ effectDashboard.summary.exposure_count }} 次</small></article>
            <article><span>物料覆盖率</span><strong>{{ formatScore(effectDashboard.summary.coverage_rate) }}</strong><small>当前有效物料 {{ effectDashboard.summary.active_campaign_count }} 个</small></article>
            <article><span>列表多样性</span><strong>{{ formatScore(effectDashboard.summary.diversity_score) }}</strong><small>基于地域与套餐标签距离</small></article>
            <article><span>平均总耗时</span><strong>{{ effectDashboard.latency.total_avg_ms }} ms</strong><small>融合 {{ effectDashboard.latency.fusion_avg_ms }} + 精排 {{ effectDashboard.latency.ranking_avg_ms }} ms</small></article>
            <article><span>P95 总耗时</span><strong>{{ effectDashboard.latency.p95_total_ms }} ms</strong><small>共 {{ effectDashboard.summary.ranking_run_count }} 次精排</small></article>
          </div>

          <div class="funnel-strip">
            <article v-for="stage in effectDashboard.funnel" :key="stage.stage">
              <div><span>{{ stage.label }}</span><strong>{{ stage.count }}</strong></div>
              <div class="funnel-track"><i :style="{ width: funnelWidth(stage.count) }"></i></div>
            </article>
          </div>

          <div class="subsection-heading"><strong>版本表现</strong><span>按反馈事件关联的精排版本聚合</span></div>
          <el-table :data="effectDashboard.version_performance" stripe>
            <el-table-column label="版本" width="90"><template #default="{ row }"><strong>{{ row.version ? `v${row.version}` : '—' }}</strong></template></el-table-column>
            <el-table-column prop="name" label="策略" min-width="190" />
            <el-table-column label="状态" width="100"><template #default="{ row }"><el-tag :type="row.is_published ? 'success' : 'info'">{{ row.is_published ? '当前发布' : '历史版本' }}</el-tag></template></el-table-column>
            <el-table-column prop="run_count" label="运行" width="75" />
            <el-table-column prop="exposure_count" label="曝光" width="75" />
            <el-table-column label="CTR" width="90"><template #default="{ row }">{{ formatScore(row.ctr) }}</template></el-table-column>
            <el-table-column label="CVR" width="90"><template #default="{ row }">{{ formatScore(row.cvr) }}</template></el-table-column>
            <el-table-column label="负反馈率" width="100"><template #default="{ row }">{{ formatScore(row.negative_rate) }}</template></el-table-column>
            <el-table-column label="覆盖 / 多样性" width="145"><template #default="{ row }">{{ formatScore(row.coverage_rate) }} / {{ formatScore(row.diversity_score) }}</template></el-table-column>
            <el-table-column label="平均总耗时" width="115"><template #default="{ row }">{{ row.total_avg_ms }} ms</template></el-table-column>
          </el-table>
          <el-empty v-if="!effectDashboard.version_performance.length" description="当前周期暂无版本运行数据" />

          <div class="effect-tables">
            <section>
              <div class="subsection-heading"><strong>每日趋势</strong><span>最近日期在下方</span></div>
              <el-table :data="effectDashboard.daily_trend" stripe max-height="360">
                <el-table-column prop="date" label="日期" width="120" />
                <el-table-column prop="exposure_count" label="曝光" width="70" />
                <el-table-column prop="click_count" label="点击" width="70" />
                <el-table-column prop="conversion_count" label="转化" width="70" />
                <el-table-column label="CTR / CVR" min-width="130"><template #default="{ row }">{{ formatScore(row.ctr) }} / {{ formatScore(row.cvr) }}</template></el-table-column>
              </el-table>
            </section>
            <section>
              <div class="subsection-heading"><strong>物料表现</strong><span>按转化、点击、曝光排序</span></div>
              <el-table :data="effectDashboard.campaign_performance" stripe max-height="360">
                <el-table-column prop="campaign_name" label="营销物料" min-width="170" />
                <el-table-column prop="exposure_count" label="曝光" width="70" />
                <el-table-column prop="click_count" label="点击" width="70" />
                <el-table-column prop="conversion_count" label="转化" width="70" />
                <el-table-column label="CTR / CVR" min-width="130"><template #default="{ row }">{{ formatScore(row.ctr) }} / {{ formatScore(row.cvr) }}</template></el-table-column>
              </el-table>
            </section>
          </div>
        </el-tab-pane>

        <el-tab-pane :label="`增量学习 ${incrementalDashboard.recent_runs.length}`" name="incremental">
          <div class="incremental-toolbar">
            <div class="section-heading">
              <strong>反馈闭环与策略迭代</strong>
              <span>同步触达/转化结果，以正负反馈的特征差异调整权重；指标不退化时可自动发布。</span>
            </div>
            <div>
              <el-button :loading="feedbackSyncLoading" @click="syncFeedback">同步业务反馈</el-button>
              <el-button type="primary" @click="openIncrementalDialog">启动增量训练</el-button>
            </div>
          </div>
          <div class="feedback-grid">
            <article v-for="eventType in incrementalDashboard.event_types" :key="eventType.value">
              <span>{{ eventType.label }}</span>
              <strong>{{ incrementalDashboard.feedback_by_type[eventType.value] || 0 }}</strong>
              <small>训练标签 {{ eventType.training_label }}</small>
            </article>
          </div>
          <el-table :data="incrementalDashboard.recent_runs" stripe>
            <el-table-column label="任务" min-width="210">
              <template #default="{ row }"><div class="primary-cell"><strong>{{ row.name }}</strong><span>学习率 {{ row.learning_rate }}</span></div></template>
            </el-table-column>
            <el-table-column label="状态" width="105">
              <template #default="{ row }"><el-tag :type="incrementalStatusType(row.status)">{{ row.status_label }}</el-tag></template>
            </el-table-column>
            <el-table-column label="版本变化" width="130">
              <template #default="{ row }">v{{ row.base_ranking_version || '—' }} → v{{ row.generated_ranking_version || '—' }}</template>
            </el-table-column>
            <el-table-column label="样本" width="130">
              <template #default="{ row }">{{ row.sample_count }}（+{{ row.positive_count }}/-{{ row.negative_count }}）</template>
            </el-table-column>
            <el-table-column label="排序准确率" width="170">
              <template #default="{ row }">
                {{ formatMetricPercent(row.metrics.base_pairwise_accuracy) }} → {{ formatMetricPercent(row.metrics.learned_pairwise_accuracy) }}
              </template>
            </el-table-column>
            <el-table-column label="发布" width="90">
              <template #default="{ row }"><el-tag size="small" :type="row.metrics.published ? 'success' : 'info'">{{ row.metrics.published ? '已发布' : '未发布' }}</el-tag></template>
            </el-table-column>
            <el-table-column label="完成时间" width="170"><template #default="{ row }">{{ formatTime(row.finished_at) }}</template></el-table-column>
          </el-table>
          <el-empty v-if="!incrementalDashboard.recent_runs.length" description="尚未启动增量训练" />

          <div class="subsection-heading">
            <strong>最近反馈事件</strong>
            <span>共 {{ incrementalDashboard.summary.feedback_count }} 条，曝光只做漏斗统计，不直接参与权重更新。</span>
          </div>
          <el-table :data="incrementalDashboard.recent_events" stripe>
            <el-table-column label="客户" min-width="150"><template #default="{ row }">{{ row.customer.name }}</template></el-table-column>
            <el-table-column label="营销物料" min-width="180"><template #default="{ row }">{{ row.campaign.name }}</template></el-table-column>
            <el-table-column label="反馈" width="105"><template #default="{ row }"><el-tag size="small">{{ row.event_type_label }}</el-tag></template></el-table-column>
            <el-table-column prop="label" label="标签" width="80" />
            <el-table-column prop="source_type" label="来源" width="150" />
            <el-table-column label="发生时间" width="170"><template #default="{ row }">{{ formatTime(row.occurred_at) }}</template></el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane :label="`精排策略 ${rankingDashboard.versions.length}`" name="ranking-versions">
          <el-table :data="rankingDashboard.versions" stripe>
            <el-table-column label="版本" width="80">
              <template #default="{ row }"><strong>v{{ row.version }}</strong></template>
            </el-table-column>
            <el-table-column label="策略" min-width="220">
              <template #default="{ row }"><div class="primary-cell"><strong>{{ row.name }}</strong><span>{{ row.metrics.baseline }}</span></div></template>
            </el-table-column>
            <el-table-column label="状态" width="105">
              <template #default="{ row }"><el-tag :type="rankingStatusType(row.status)">{{ row.status_label }}</el-tag></template>
            </el-table-column>
            <el-table-column label="特征权重" min-width="360">
              <template #default="{ row }">
                <el-tag v-for="feature in row.feature_schema" :key="feature.value" size="small" effect="plain">
                  {{ feature.label }} {{ formatWeight(row.feature_weights[feature.value]) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="发布时间" width="170">
              <template #default="{ row }">{{ formatTime(row.published_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="90" fixed="right">
              <template #default="{ row }">
                <el-button v-if="row.status !== 'PUBLISHED'" link type="primary" @click="publishRanking(row.id)">发布</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane :label="`精排记录 ${rankingDashboard.recent_runs.length}`" name="ranking-history">
          <el-table :data="rankingDashboard.recent_runs" stripe>
            <el-table-column label="客户" min-width="170"><template #default="{ row }">{{ row.customer.name }}</template></el-table-column>
            <el-table-column label="策略" width="90"><template #default="{ row }">{{ row.ranking_version ? `v${row.ranking_version}` : '—' }}</template></el-table-column>
            <el-table-column prop="candidate_count" label="候选数" width="90" />
            <el-table-column prop="top_n" label="TopN" width="80" />
            <el-table-column label="首位物料" min-width="190"><template #default="{ row }">{{ row.ranked_candidates[0]?.campaign_name || '—' }}</template></el-table-column>
            <el-table-column prop="latency_ms" label="精排耗时(ms)" width="125" />
            <el-table-column label="执行时间" width="170"><template #default="{ row }">{{ formatTime(row.create_time) }}</template></el-table-column>
          </el-table>
          <el-empty v-if="!rankingDashboard.recent_runs.length" description="暂无精排运行记录" />
        </el-tab-pane>

        <el-tab-pane :label="`模型版本 ${dashboard.model_versions.length}`" name="models">
          <el-table :data="dashboard.model_versions" stripe>
            <el-table-column label="版本" width="90">
              <template #default="{ row }"><strong>v{{ row.version }}</strong></template>
            </el-table-column>
            <el-table-column label="模型" min-width="220">
              <template #default="{ row }">
                <div class="primary-cell"><strong>{{ row.name }}</strong><span>特征快照 v{{ row.snapshot_version }}</span></div>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="105">
              <template #default="{ row }"><el-tag :type="modelStatusType(row.status)">{{ row.status_label }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="embedding_dim" label="向量维度" width="100" />
            <el-table-column prop="item_embedding_count" label="物料向量" width="100" />
            <el-table-column label="最终损失" width="110">
              <template #default="{ row }">{{ formatLoss(row.metrics.final_loss) }}</template>
            </el-table-column>
            <el-table-column label="准确率" width="100">
              <template #default="{ row }">{{ formatPercent(row.metrics.accuracy) }}</template>
            </el-table-column>
            <el-table-column label="发布时间" width="170">
              <template #default="{ row }">{{ formatTime(row.published_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="90" fixed="right">
              <template #default="{ row }">
                <el-button v-if="row.status !== 'PUBLISHED'" link type="primary" @click="publishModel(row.id)">
                  发布
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!dashboard.model_versions.length" description="暂无模型版本" />
        </el-tab-pane>

        <el-tab-pane :label="`训练记录 ${dashboard.training_runs.length}`" name="training">
          <el-table :data="dashboard.training_runs" stripe>
            <el-table-column label="任务" min-width="220">
              <template #default="{ row }">
                <div class="primary-cell"><strong>{{ row.name }}</strong><span>快照 v{{ row.snapshot_version }}</span></div>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }"><el-tag :type="runStatusType(row.status)">{{ row.status_label }}</el-tag></template>
            </el-table-column>
            <el-table-column label="样本" width="110">
              <template #default="{ row }">{{ row.positive_count }} / {{ row.sample_count }}</template>
            </el-table-column>
            <el-table-column prop="epochs" label="轮数" width="75" />
            <el-table-column label="损失变化" min-width="150">
              <template #default="{ row }">{{ formatLoss(row.initial_loss) }} → {{ formatLoss(row.final_loss) }}</template>
            </el-table-column>
            <el-table-column label="完成时间" width="170">
              <template #default="{ row }">{{ formatTime(row.finished_at) }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!dashboard.training_runs.length" description="暂无训练记录" />
        </el-tab-pane>

        <el-tab-pane :label="`物料向量 ${dashboard.item_embeddings.length}`" name="vectors">
          <el-table :data="dashboard.item_embeddings" stripe>
            <el-table-column prop="campaign_name" label="营销物料" min-width="240" />
            <el-table-column prop="dimension" label="向量维度" width="120" />
            <el-table-column label="L2 范数" width="140">
              <template #default="{ row }">{{ Number(row.vector_norm).toFixed(6) }}</template>
            </el-table-column>
            <el-table-column label="更新时间" width="180">
              <template #default="{ row }">{{ formatTime(row.update_time) }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!dashboard.item_embeddings.length" description="已发布模型尚无物料向量" />
        </el-tab-pane>

        <el-tab-pane :label="`融合记录 ${fusionDashboard.recent_runs.length}`" name="fusion-history">
          <el-table :data="fusionDashboard.recent_runs" stripe>
            <el-table-column label="客户" min-width="180"><template #default="{ row }">{{ row.customer.name }}</template></el-table-column>
            <el-table-column label="模型" width="90"><template #default="{ row }">{{ row.model_version ? `v${row.model_version}` : '—' }}</template></el-table-column>
            <el-table-column prop="top_k" label="TopK" width="80" />
            <el-table-column label="返回物料" width="100"><template #default="{ row }">{{ row.fused_candidates.length }}</template></el-table-column>
            <el-table-column prop="latency_ms" label="耗时(ms)" width="100" />
            <el-table-column label="启用通道" min-width="220">
              <template #default="{ row }">{{ row.config_snapshot.enabled_channels.join(' / ') }}</template>
            </el-table-column>
            <el-table-column label="执行时间" width="170"><template #default="{ row }">{{ formatTime(row.create_time) }}</template></el-table-column>
          </el-table>
          <el-empty v-if="!fusionDashboard.recent_runs.length" description="暂无融合召回记录" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="trainDialogVisible" title="启动轻量双塔训练" width="560px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="训练任务名称">
          <el-input v-model="trainForm.name" placeholder="例如：双塔召回基线-v1" />
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="物料向量维度">
            <el-input-number v-model="trainForm.embedding_dim" :min="4" :max="64" />
          </el-form-item>
          <el-form-item label="训练轮数">
            <el-input-number v-model="trainForm.epochs" :min="1" :max="300" />
          </el-form-item>
          <el-form-item label="学习率">
            <el-input-number v-model="trainForm.learning_rate" :min="0.0001" :max="1" :step="0.01" :precision="4" />
          </el-form-item>
          <el-form-item label="训练完成后自动发布">
            <el-switch v-model="trainForm.auto_publish" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="trainDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="trainLoading" @click="startTraining">开始训练</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="fusionConfigVisible" title="多路召回融合配置" width="680px" destroy-on-close>
      <el-alert title="权重无需手工归一到 100%，系统会按启用通道的权重总和自动归一。" type="info" :closable="false" />
      <el-checkbox-group v-model="fusionConfig.enabled_channels" class="weight-grid">
        <div v-for="channel in fusionConfig.channels" :key="channel.value" class="weight-row">
          <el-checkbox :value="channel.value">{{ channel.label }}</el-checkbox>
          <el-input-number v-model="fusionConfig.weights[channel.value]" :min="0" :max="10" :step="0.05" :precision="2" />
        </div>
      </el-checkbox-group>
      <el-form label-position="top">
        <el-form-item label="单通道候选池大小">
          <el-input-number v-model="fusionConfig.candidate_pool_size" :min="5" :max="200" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="fusionConfigVisible = false">取消</el-button>
        <el-button type="primary" :loading="configLoading" @click="saveFusionConfig">保存配置</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="rankingConfigVisible" title="新建精排策略版本" width="720px" destroy-on-close>
      <el-alert title="系统会自动归一化权重；新版本保留完整特征定义，发布后旧版本自动归档。" type="info" :closable="false" />
      <el-form label-position="top" class="ranking-form">
        <el-form-item label="策略名称">
          <el-input v-model="rankingDraft.name" placeholder="例如：业务适配增强精排-v2" />
        </el-form-item>
        <div class="weight-grid">
          <div v-for="feature in rankingDashboard.feature_schema" :key="feature.value" class="weight-row">
            <span>{{ feature.label }}</span>
            <el-input-number v-model="rankingDraft.feature_weights[feature.value]" :min="0" :max="10" :step="0.05" :precision="2" />
          </div>
        </div>
        <el-form-item label="创建后立即发布">
          <el-switch v-model="rankingDraft.auto_publish" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rankingConfigVisible = false">取消</el-button>
        <el-button type="primary" :loading="rankingConfigLoading" @click="createRankingVersion">创建版本</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="incrementalDialogVisible" title="启动反馈增量训练" width="580px" destroy-on-close>
      <el-alert title="训练会固化本次事件快照并生成新精排版本；开启自动发布时，仅在排序准确率不低于基线时发布。" type="info" :closable="false" />
      <el-form label-position="top" class="ranking-form">
        <el-form-item label="任务名称">
          <el-input v-model="incrementalForm.name" placeholder="例如：反馈增量精排-v3" />
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="学习率">
            <el-input-number v-model="incrementalForm.learning_rate" :min="0.01" :max="1" :step="0.05" :precision="2" />
          </el-form-item>
          <el-form-item label="最小有效样本数">
            <el-input-number v-model="incrementalForm.minimum_samples" :min="2" :max="10000" />
          </el-form-item>
        </div>
        <el-form-item label="指标不退化时自动发布">
          <el-switch v-model="incrementalForm.auto_publish" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="incrementalDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="incrementalTrainLoading" @click="startIncrementalTraining">开始训练</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Connection, Cpu, Files, Refresh, Search, Setting } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref, toRaw } from 'vue'

import {
  buildRecommendationFeatureSnapshot,
  createRecommendationRankingVersion,
  getRecommendationDashboard,
  getRecommendationEffectDashboard,
  getRecommendationFusionDashboard,
  getRecommendationIncrementalDashboard,
  getRecommendationRankingDashboard,
  inferRecommendation,
  inferRecommendationFusion,
  inferRecommendationRanking,
  publishRecommendationModel,
  publishRecommendationRankingVersion,
  recordRecommendationFeedback,
  saveRecommendationFusionConfig,
  syncRecommendationFeedback,
  trainRecommendationIncremental,
  trainRecommendationModel,
  type RecommendationDashboard,
  type RecommendationEffectDashboard,
  type RecommendationFusionConfig,
  type RecommendationFusionDashboard,
  type RecommendationFusionResult,
  type RecommendationInferenceResult,
  type RecommendationIncrementalDashboard,
  type RecommendationIncrementalStatus,
  type RecommendationIncrementalTrainRequest,
  type RecommendationModelStatus,
  type RecommendationFeedbackType,
  type RecommendationRankingDashboard,
  type RecommendationRankingResult,
  type RecommendationRankingStatus,
  type RecommendationRankingVersion,
  type RecommendationTrainingStatus,
  type RecommendationTrainRequest,
} from '@/api/marketing/recommendation-engine'
import { datetimeFormat } from '@/utils/time'

const emptyDashboard = (): RecommendationDashboard => ({
  summary: {
    snapshot_version: null,
    user_feature_count: 0,
    item_feature_count: 0,
    successful_run_count: 0,
    model_version_count: 0,
    published_version: null,
    inference_count: 0,
  },
  training_runs: [],
  model_versions: [],
  item_embeddings: [],
  customers: [],
})

const emptyFusionConfig = (): RecommendationFusionConfig => ({
  weights: {
    TWO_TOWER: 0.35,
    RULE: 0.2,
    COLLABORATIVE: 0.15,
    CONTENT: 0.15,
    HOT: 0.1,
    REGION: 0.05,
  },
  enabled_channels: ['TWO_TOWER', 'RULE', 'COLLABORATIVE', 'CONTENT', 'HOT', 'REGION'],
  candidate_pool_size: 50,
  channels: [
    { value: 'TWO_TOWER', label: '双塔召回' },
    { value: 'RULE', label: '业务规则' },
    { value: 'COLLABORATIVE', label: '协同过滤' },
    { value: 'CONTENT', label: '内容相似' },
    { value: 'HOT', label: '全局热度' },
    { value: 'REGION', label: '地域召回' },
  ],
  update_time: '',
})

const emptyFusionDashboard = (): RecommendationFusionDashboard => ({
  config: emptyFusionConfig(),
  summary: { fusion_run_count: 0, active_channel_count: 6, latest_latency_ms: null },
  recent_runs: [],
})

const defaultRankingWeights = (): RecommendationRankingVersion['feature_weights'] => ({
  RECALL_SCORE: 0.4,
  BUSINESS_MATCH: 0.16,
  REGION_FIT: 0.1,
  PLAN_FIT: 0.1,
  USAGE_FIT: 0.08,
  CHANNEL_COVERAGE: 0.1,
  PRIORITY_SCORE: 0.06,
})

const emptyRankingDashboard = (): RecommendationRankingDashboard => ({
  summary: { ranking_version_count: 0, published_version: null, ranking_run_count: 0, latest_latency_ms: null },
  feature_schema: [],
  versions: [],
  recent_runs: [],
})

const emptyIncrementalDashboard = (): RecommendationIncrementalDashboard => ({
  summary: {
    feedback_count: 0,
    labeled_sample_count: 0,
    positive_count: 0,
    negative_count: 0,
    incremental_run_count: 0,
    latest_generated_version: null,
  },
  feedback_by_type: { EXPOSED: 0, CLICKED: 0, CONVERTED: 0, NEGATIVE: 0 },
  event_types: [],
  recent_events: [],
  recent_runs: [],
})

const emptyEffectDashboard = (): RecommendationEffectDashboard => ({
  period: { days: 30, start_at: '', end_at: '' },
  summary: {
    exposure_count: 0,
    click_count: 0,
    conversion_count: 0,
    negative_count: 0,
    ctr: 0,
    cvr: 0,
    negative_rate: 0,
    coverage_rate: 0,
    diversity_score: 0,
    unique_customer_count: 0,
    active_campaign_count: 0,
    ranking_run_count: 0,
  },
  latency: { ranking_avg_ms: 0, fusion_avg_ms: 0, total_avg_ms: 0, p95_total_ms: 0 },
  funnel: [],
  daily_trend: [],
  version_performance: [],
  campaign_performance: [],
})

const dashboard = ref<RecommendationDashboard>(emptyDashboard())
const fusionDashboard = ref<RecommendationFusionDashboard>(emptyFusionDashboard())
const rankingDashboard = ref<RecommendationRankingDashboard>(emptyRankingDashboard())
const incrementalDashboard = ref<RecommendationIncrementalDashboard>(emptyIncrementalDashboard())
const effectDashboard = ref<RecommendationEffectDashboard>(emptyEffectDashboard())
const fusionConfig = ref<RecommendationFusionConfig>(emptyFusionConfig())
const pageLoading = ref(false)
const snapshotLoading = ref(false)
const trainLoading = ref(false)
const inferenceLoading = ref(false)
const fusionLoading = ref(false)
const rankingLoading = ref(false)
const configLoading = ref(false)
const rankingConfigLoading = ref(false)
const feedbackSyncLoading = ref(false)
const incrementalTrainLoading = ref(false)
const effectLoading = ref(false)
const trainDialogVisible = ref(false)
const fusionConfigVisible = ref(false)
const rankingConfigVisible = ref(false)
const incrementalDialogVisible = ref(false)
const activeTab = ref('ranking')
const effectPeriod = ref<7 | 30 | 90>(30)
const inferenceResult = ref<RecommendationInferenceResult | null>(null)
const fusionResult = ref<RecommendationFusionResult | null>(null)
const rankingResult = ref<RecommendationRankingResult | null>(null)
const inferenceForm = ref({ customer_id: '', top_k: 5 })
const fusionForm = ref({ customer_id: '', top_k: 5 })
const rankingForm = ref({ customer_id: '', top_n: 5, candidate_pool_size: 30 })
const rankingDraft = ref({ name: '', feature_weights: defaultRankingWeights(), auto_publish: true })
const incrementalForm = ref<RecommendationIncrementalTrainRequest>({
  name: '',
  learning_rate: 0.25,
  minimum_samples: 2,
  auto_publish: true,
})
const trainForm = ref<RecommendationTrainRequest>({
  name: '',
  embedding_dim: 16,
  epochs: 40,
  learning_rate: 0.03,
  auto_publish: true,
})

function clonePlainData<T extends object>(value: T): T {
  return structuredClone(toRaw(value))
}

function modelStatusType(status: RecommendationModelStatus) {
  return status === 'PUBLISHED' ? 'success' : status === 'ARCHIVED' ? 'info' : 'warning'
}

function runStatusType(status: RecommendationTrainingStatus) {
  return status === 'SUCCESS' ? 'success' : status === 'FAILED' ? 'danger' : 'warning'
}

function rankingStatusType(status: RecommendationRankingStatus) {
  return status === 'PUBLISHED' ? 'success' : status === 'ARCHIVED' ? 'info' : 'warning'
}

function incrementalStatusType(status: RecommendationIncrementalStatus) {
  return status === 'SUCCESS' ? 'success' : status === 'FAILED' ? 'danger' : 'warning'
}

function formatTime(value?: string | null) {
  return value ? datetimeFormat(value) : '—'
}

function formatLoss(value?: number | null) {
  return typeof value === 'number' ? value.toFixed(6) : '—'
}

function formatPercent(value?: number) {
  return typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : '—'
}

function formatScore(value: number) {
  return `${(value * 100).toFixed(2)}%`
}

function formatWeight(value: number) {
  return `${(value * 100).toFixed(0)}%`
}

function formatMetricPercent(value: unknown) {
  return typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : '—'
}

const enabledChannelOptions = computed(() =>
  fusionConfig.value.channels.filter((channel) => fusionConfig.value.enabled_channels.includes(channel.value)),
)

const funnelMaxCount = computed(() => Math.max(1, ...effectDashboard.value.funnel.map((row) => row.count)))

function funnelWidth(count: number) {
  return count ? `${Math.max(4, (count / funnelMaxCount.value) * 100)}%` : '0%'
}

async function loadDashboard() {
  pageLoading.value = true
  try {
    const [engineResponse, fusionResponse, rankingResponse, incrementalResponse, effectResponse] = await Promise.all([
      getRecommendationDashboard(),
      getRecommendationFusionDashboard(),
      getRecommendationRankingDashboard(),
      getRecommendationIncrementalDashboard(),
      getRecommendationEffectDashboard(effectPeriod.value),
    ])
    dashboard.value = engineResponse.data
    fusionDashboard.value = fusionResponse.data
    rankingDashboard.value = rankingResponse.data
    incrementalDashboard.value = incrementalResponse.data
    effectDashboard.value = effectResponse.data
    fusionConfig.value = clonePlainData(fusionResponse.data.config)
    if (!inferenceForm.value.customer_id && dashboard.value.customers.length) {
      inferenceForm.value.customer_id = dashboard.value.customers[0].id
    }
    if (!fusionForm.value.customer_id && dashboard.value.customers.length) {
      fusionForm.value.customer_id = dashboard.value.customers[0].id
    }
    if (!rankingForm.value.customer_id && dashboard.value.customers.length) {
      rankingForm.value.customer_id = dashboard.value.customers[0].id
    }
  } finally {
    pageLoading.value = false
  }
}

async function loadEffectDashboard() {
  effectDashboard.value = (await getRecommendationEffectDashboard(effectPeriod.value, effectLoading)).data
}

async function createSnapshot() {
  const result = await buildRecommendationFeatureSnapshot(64, snapshotLoading)
  await loadDashboard()
  ElMessage.success(`特征快照 v${result.data.snapshot_version} 已生成`)
}

function openTrainDialog() {
  if (!dashboard.value.summary.snapshot_version) {
    ElMessage.warning('请先生成用户与物料特征快照')
    return
  }
  trainForm.value.name ||= `双塔召回基线-v${dashboard.value.summary.snapshot_version}`
  trainDialogVisible.value = true
}

function openFusionConfig() {
  fusionConfig.value = clonePlainData(fusionDashboard.value.config)
  fusionConfigVisible.value = true
}

function openRankingConfig() {
  const published = rankingDashboard.value.versions.find((row) => row.status === 'PUBLISHED')
  rankingDraft.value = {
    name: `可解释加权精排-v${rankingDashboard.value.summary.ranking_version_count + 1}`,
    feature_weights: clonePlainData(published?.feature_weights || defaultRankingWeights()),
    auto_publish: true,
  }
  rankingConfigVisible.value = true
}

async function startTraining() {
  const request = {
    ...trainForm.value,
    snapshot_version: dashboard.value.summary.snapshot_version || undefined,
  }
  const result = await trainRecommendationModel(request, trainLoading)
  trainDialogVisible.value = false
  await loadDashboard()
  activeTab.value = 'models'
  ElMessage.success(`模型 v${result.data.model_version.version} 训练完成`)
}

async function publishModel(id: string) {
  const result = await publishRecommendationModel(id)
  await loadDashboard()
  ElMessage.success(`模型 v${result.data.version} 已发布`)
}

async function runInference() {
  if (!inferenceForm.value.customer_id) return
  inferenceResult.value = (
    await inferRecommendation(
      { customer_id: inferenceForm.value.customer_id, top_k: inferenceForm.value.top_k },
      inferenceLoading,
    )
  ).data
  dashboard.value.summary.inference_count += 1
  ElMessage.success(`已召回 ${inferenceResult.value.candidates.length} 个营销物料`)
}

async function runFusionInference() {
  if (!fusionForm.value.customer_id) return
  fusionResult.value = (
    await inferRecommendationFusion(
      { customer_id: fusionForm.value.customer_id, top_k: fusionForm.value.top_k },
      fusionLoading,
    )
  ).data
  await loadDashboard()
  ElMessage.success(`已融合召回 ${fusionResult.value.candidates.length} 个营销物料`)
}

async function runRankingInference() {
  if (!rankingForm.value.customer_id) return
  rankingResult.value = (await inferRecommendationRanking(rankingForm.value, rankingLoading)).data
  await loadDashboard()
  ElMessage.success(`已从 ${rankingResult.value.candidate_count} 个候选中输出 Top${rankingResult.value.candidates.length}`)
}

async function recordFeedback(
  campaignId: string,
  eventType: Exclude<RecommendationFeedbackType, 'EXPOSED'>,
) {
  if (!rankingResult.value) return
  const result = await recordRecommendationFeedback({
    ranking_run_id: rankingResult.value.ranking_run_id,
    campaign_id: campaignId,
    event_type: eventType,
    event_key: `manual:${rankingResult.value.ranking_run_id}:${campaignId}:${eventType}`,
  })
  await loadDashboard()
  ElMessage.success(result.data.created ? '反馈已记录并进入增量样本池' : '该反馈已记录')
}

async function syncFeedback() {
  const result = await syncRecommendationFeedback(feedbackSyncLoading)
  await loadDashboard()
  ElMessage.success(`业务反馈同步完成，新增 ${result.data.created_count} 条`)
}

function openIncrementalDialog() {
  incrementalForm.value.name = `反馈增量精排-v${rankingDashboard.value.summary.ranking_version_count + 1}`
  incrementalDialogVisible.value = true
}

async function startIncrementalTraining() {
  const result = await trainRecommendationIncremental(incrementalForm.value, incrementalTrainLoading)
  incrementalDialogVisible.value = false
  await loadDashboard()
  activeTab.value = 'incremental'
  ElMessage.success(
    `精排策略 v${result.data.generated_version.version} 已生成${result.data.generated_version.status === 'PUBLISHED' ? '并发布' : ''}`,
  )
}

async function createRankingVersion() {
  const result = await createRecommendationRankingVersion(rankingDraft.value, rankingConfigLoading)
  rankingConfigVisible.value = false
  await loadDashboard()
  activeTab.value = 'ranking-versions'
  ElMessage.success(`精排策略 v${result.data.version} 已创建${result.data.status === 'PUBLISHED' ? '并发布' : ''}`)
}

async function publishRanking(id: string) {
  const result = await publishRecommendationRankingVersion(id)
  await loadDashboard()
  ElMessage.success(`精排策略 v${result.data.version} 已发布`)
}

async function saveFusionConfig() {
  if (!fusionConfig.value.enabled_channels.length) {
    ElMessage.warning('至少启用一个召回通道')
    return
  }
  const result = await saveRecommendationFusionConfig(
    {
      weights: fusionConfig.value.weights,
      enabled_channels: fusionConfig.value.enabled_channels,
      candidate_pool_size: fusionConfig.value.candidate_pool_size,
    },
    configLoading,
  )
  fusionConfig.value = clonePlainData(result.data)
  fusionDashboard.value.config = clonePlainData(result.data)
  fusionDashboard.value.summary.active_channel_count = result.data.enabled_channels.length
  fusionConfigVisible.value = false
  ElMessage.success('融合权重配置已保存')
}

onMounted(loadDashboard)
</script>

<style scoped lang="scss">
.recommendation-page {
  --ink: #17343d;
  --muted: #687d84;
  --line: #dce6e8;
  height: 100%;
  padding: 22px 26px 36px;
  overflow-y: auto;
  color: var(--ink);
  background: #f3f7f7;
}
.hero, .hero-actions, .section-heading, .result-meta, .result-meta > div {
  display: flex;
}
.hero { align-items: center; justify-content: space-between; gap: 24px; margin-bottom: 18px; }
.hero h2 { margin: 5px 0 2px; font-size: 27px; letter-spacing: -.5px; }
.hero p { margin: 0; color: var(--muted); }
.eyebrow { color: #087d74; font-family: monospace; font-size: 12px; font-weight: 700; letter-spacing: 1px; }
.hero-actions { gap: 8px; }
.summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 12px; }
.summary-grid article { padding: 16px 18px; border: 1px solid var(--line); border-radius: 7px; background: #fff; }
.summary-grid span, .summary-grid small { display: block; color: var(--muted); }
.summary-grid strong { display: block; margin: 8px 0 4px; font-size: 29px; }
.summary-grid .published-card { border-top: 3px solid #0c8a7e; }
.summary-grid .fusion-card { border-top: 3px solid #3d65c7; }
.summary-grid .ranking-card { border-top: 3px solid #8a55b6; }
.summary-grid .incremental-card { border-top: 3px solid #db8b34; }
.summary-grid .effect-card { border-top: 3px solid #c84c5a; }
.summary-grid .effect-card strong { font-size: 21px; }
.baseline-note { margin-bottom: 12px; }
.workbench { border-color: var(--line); }
.inference-layout { display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 22px; min-height: 390px; }
.inference-form { padding: 18px; border: 1px solid var(--line); border-radius: 7px; background: #f8fbfb; }
.section-heading { flex-direction: column; gap: 4px; margin-bottom: 20px; }
.section-heading span, .primary-cell span { color: var(--muted); font-size: 12px; }
.inference-form .el-button, .el-select, .el-input-number { width: 100%; }
.result-meta { gap: 10px; margin-bottom: 14px; }
.result-meta > div { min-width: 130px; padding: 10px 13px; flex-direction: column; gap: 3px; border-radius: 6px; background: #eef5f4; }
.result-meta span { color: var(--muted); font-size: 12px; }
.primary-cell { display: grid; gap: 4px; }
.score { color: #087d74; font-family: monospace; }
.inference-result .el-tag { margin: 2px 4px 2px 0; }
.channel-preview { display: grid; gap: 8px; margin: 4px 0 20px; }
.channel-preview > span { color: var(--muted); font-size: 13px; }
.source-detail { display: grid; gap: 6px; }
.source-detail span, .source-detail p { color: var(--muted); font-size: 12px; }
.source-detail p { margin: 0; }
.weight-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 18px; margin: 18px 0; }
.weight-row { display: grid; grid-template-columns: 1fr 130px; align-items: center; gap: 12px; padding: 10px 12px; border: 1px solid var(--line); border-radius: 6px; }
.weight-row .el-input-number { width: 130px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 18px; }
.compact-grid { gap: 0 10px; }
.ranking-form { margin-top: 18px; }
.incremental-toolbar { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; margin-bottom: 16px; }
.feedback-grid { display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); gap: 10px; margin-bottom: 18px; }
.feedback-grid article { padding: 13px 15px; border: 1px solid var(--line); border-radius: 6px; background: #f8fbfb; }
.feedback-grid span, .feedback-grid small { display: block; color: var(--muted); }
.feedback-grid strong { display: block; margin: 5px 0; font-size: 22px; }
.effect-toolbar { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; margin-bottom: 16px; }
.period-select { width: 130px; }
.effect-grid { display: grid; grid-template-columns: repeat(3, minmax(150px, 1fr)); gap: 10px; margin-bottom: 18px; }
.effect-grid article { padding: 13px 15px; border: 1px solid var(--line); border-radius: 6px; background: #f8fbfb; }
.effect-grid span, .effect-grid small { display: block; color: var(--muted); }
.effect-grid strong { display: block; margin: 5px 0; font-size: 22px; }
.funnel-strip { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 10px; margin-bottom: 20px; }
.funnel-strip article { padding: 12px 14px; border-radius: 6px; background: #eef5f4; }
.funnel-strip article > div:first-child { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; margin-bottom: 9px; }
.funnel-strip span { color: var(--muted); font-size: 12px; }
.funnel-strip strong { font-size: 18px; }
.funnel-track { height: 7px; overflow: hidden; border-radius: 999px; background: #d8e7e5; }
.funnel-track i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #0c8a7e, #51b7aa); }
.effect-tables { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 18px; }
.subsection-heading { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; margin: 26px 0 12px; }
.subsection-heading span { color: var(--muted); font-size: 12px; }
@media (max-width: 1050px) {
  .summary-grid { grid-template-columns: repeat(2, 1fr); }
  .inference-layout { grid-template-columns: 1fr; }
  .feedback-grid, .effect-grid { grid-template-columns: repeat(2, 1fr); }
  .effect-tables { grid-template-columns: 1fr; }
}
@media (max-width: 760px) {
  .recommendation-page { padding: 16px; }
  .hero { align-items: flex-start; flex-direction: column; }
  .hero-actions { flex-wrap: wrap; }
  .summary-grid, .form-grid, .weight-grid { grid-template-columns: 1fr; }
  .result-meta { flex-direction: column; }
  .incremental-toolbar, .effect-toolbar, .subsection-heading { align-items: flex-start; flex-direction: column; }
  .feedback-grid, .effect-grid, .funnel-strip { grid-template-columns: 1fr; }
}
</style>
