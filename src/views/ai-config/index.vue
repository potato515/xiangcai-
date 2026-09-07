<template>
  <div class="ai-config-page">
    <a-card title="AI配置中心" :bordered="false">
      <a-tabs v-model:active-key="activeTab" type="card">
        <!-- 文章类型管理 -->
        <a-tab-pane key="types" title="文章类型">
          <div class="config-section">
            <div class="section-header">
              <span>文章类型管理（选择类型后使用对应提示词生成文章）</span>
              <a-button type="primary" size="small" @click="showTypeModal()">新增类型</a-button>
            </div>
            <a-table :data="pagedArticleTypes" :pagination="articleTypePagination" size="small" row-key="id" @page-change="handleArticleTypePageChange" @page-size-change="handleArticleTypePageSizeChange">
              <template #columns>
                <a-table-column title="ID" data-index="id" :width="60" />
                <a-table-column title="类型名称" data-index="name" :width="150" />
                <a-table-column title="文章生成提示词" data-index="prompt">
                  <template #cell="{ record }">
                    <span class="prompt-text">{{ record.prompt || '（未设置）' }}</span>
                  </template>
                </a-table-column>
                <a-table-column title="操作" :width="150">
                  <template #cell="{ record }">
                    <a-button size="mini" type="text" @click="showTypeModal(record)">编辑</a-button>
                    <a-button size="mini" type="text" status="danger" @click="deleteType(record)">删除</a-button>
                  </template>
                </a-table-column>
              </template>
            </a-table>
            <a-empty v-if="articleTypes.length === 0" description="暂无文章类型，请点击右上角新增" />
          </div>
        </a-tab-pane>

        <!-- 提示词管理 -->
        <a-tab-pane key="prompts" title="提示词管理">
          <div class="config-section">
            <a-form layout="vertical">
              <a-form-item label="默认文章生成提示词（未选择文章类型时使用）">
                <a-textarea
                  v-model="prompts.default_article_prompt"
                  :auto-size="{ minRows: 6, maxRows: 12 }"
                  placeholder="请输入默认文章生成提示词，例如：请根据以下标题写一篇家庭伦理故事，要求情节曲折、冲突强烈..."
                />
              </a-form-item>
              <a-form-item label="图片生成基础提示词（生成图片时的基础风格描述）">
                <a-textarea
                  v-model="prompts.image_prompt"
                  :auto-size="{ minRows: 4, maxRows: 8 }"
                  placeholder="请输入图片生成基础提示词，例如：写实风格，温暖色调，家庭场景，高清晰度..."
                />
              </a-form-item>
              <a-form-item>
                <a-button type="primary" :loading="savingPrompts" @click="savePrompts">保存提示词</a-button>
              </a-form-item>
            </a-form>
          </div>
        </a-tab-pane>

        <!-- AI账号管理 -->
        <a-tab-pane key="accounts" title="AI账号">
          <div class="config-section">
            <a-radio-group v-model="accountPlatform" type="button" @change="loadAccounts">
              <a-radio value="zhipu">智谱AI</a-radio>
              <a-radio value="yuanbao">腾讯元宝</a-radio>
              <a-radio value="doubao">豆包</a-radio>
            </a-radio-group>

            <div class="section-header" style="margin-top: 16px;">
              <span>{{ platformNames[accountPlatform] }}账号列表</span>
              <a-button type="primary" size="small" @click="showAccountModal()">新增账号</a-button>
            </div>

            <a-table :data="pagedAccounts" :pagination="accountPagination" size="small" row-key="id" @page-change="handleAccountPageChange" @page-size-change="handleAccountPageSizeChange">
              <template #columns>
                <a-table-column title="ID" data-index="id" :width="60" />
                <a-table-column title="账号名称" data-index="name" :width="120" />
                <a-table-column title="账号标识" data-index="account_id" :width="150" />
                <a-table-column v-if="accountPlatform === 'yuanbao'" title="模型" data-index="model" :width="100" />
                <a-table-column title="备注" data-index="remark" />
                <a-table-column title="操作" :width="150">
                  <template #cell="{ record }">
                    <a-button size="mini" type="text" @click="showAccountModal(record)">编辑</a-button>
                    <a-button size="mini" type="text" status="danger" @click="deleteAccount(record)">删除</a-button>
                  </template>
                </a-table-column>
              </template>
            </a-table>
            <a-empty v-if="accounts.length === 0" description="暂无账号，请点击右上角新增" />
          </div>
        </a-tab-pane>

        <!-- 生成设置 -->
        <a-tab-pane key="settings" title="生成设置">
          <div class="config-section">
            <a-form layout="vertical">
              <a-divider orientation="left">基础设置</a-divider>
              <a-form-item label="每个段落默认备选图片数量">
                <a-input-number v-model="settings.default_image_count" :min="1" :max="10" />
              </a-form-item>
              <a-form-item label="默认AI平台">
                <a-select v-model="settings.default_ai_platform" style="width: 200px;">
                  <a-option value="zhipu">智谱AI</a-option>
                  <a-option value="yuanbao">腾讯元宝</a-option>
                  <a-option value="doubao">豆包</a-option>
                </a-select>
              </a-form-item>
              <a-form-item label="默认文章付费类型">
                <a-select v-model="settings.default_article_type" style="width: 200px;">
                  <a-option value="free">免费类型</a-option>
                  <a-option value="paid">付费类型</a-option>
                </a-select>
              </a-form-item>

              <a-divider orientation="left">批量生成默认配置（文章中心页面启动批量生成时使用）</a-divider>
              <a-row :gutter="24">
                <a-col :span="12">
                  <a-form-item label="文章生成AI平台" required>
                    <a-select v-model="batchConfig.article_platform" style="width: 100%;">
                      <a-option value="zhipu">智谱AI</a-option>
                      <a-option value="doubao">豆包</a-option>
                      <a-option value="yuanbao">腾讯元宝</a-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="文章生成默认账号" required>
                    <a-select v-model="batchConfig.article_account_id" style="width: 100%;" placeholder="请选择账号">
                      <a-option v-for="acc in articlePlatformAccounts" :key="acc.id" :value="acc.account_id">
                        {{ acc.name }}（{{ acc.account_id }}）
                      </a-option>
                    </a-select>
                  </a-form-item>
                </a-col>
              </a-row>
              <a-row :gutter="24">
                <a-col :span="12">
                  <a-form-item label="图片生成AI平台">
                    <a-select v-model="batchConfig.image_platform" style="width: 100%;">
                      <a-option value="doubao">豆包</a-option>
                      <a-option value="zhipu">智谱AI</a-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="每章节备选图片数量">
                    <a-input-number v-model="batchConfig.image_count_per_chapter" :min="1" :max="10" style="width: 100%;" />
                  </a-form-item>
                </a-col>
              </a-row>
              <a-form-item label="是否自动生成配套图片">
                <a-switch v-model="batchConfig.generate_images" />
                <span style="margin-left: 8px; font-size: 12px; color: #86909c;">
                  开启后，文章生成成功后会自动调用豆包AI为每个章节生成备选图片
                </span>
              </a-form-item>

              <a-form-item>
                <a-button type="primary" :loading="savingSettings" @click="saveSettings">保存全部设置</a-button>
              </a-form-item>
            </a-form>
          </div>
        </a-tab-pane>
      </a-tabs>
    </a-card>

    <!-- 文章类型弹窗 -->
    <a-modal
      v-model:visible="typeModalVisible"
      :title="editingType ? '编辑文章类型' : '新增文章类型'"
      @ok="saveType"
    >
      <a-form layout="vertical">
        <a-form-item label="类型名称" required>
          <a-input v-model="typeForm.name" placeholder="例如：家庭伦理、职场故事" />
        </a-form-item>
        <a-form-item label="文章生成提示词">
          <a-textarea
            v-model="typeForm.prompt"
            :auto-size="{ minRows: 5, maxRows: 10 }"
            placeholder="请输入该类型的文章生成提示词，程序会直接将此提示词+标题发送给AI"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 账号弹窗 -->
    <a-modal
      v-model:visible="accountModalVisible"
      :title="editingAccount ? '编辑账号' : '新增账号'"
      @ok="saveAccount"
    >
      <a-form layout="vertical">
        <a-form-item label="账号名称" required>
          <a-input v-model="accountForm.name" placeholder="给这个账号起个名字，方便识别" />
        </a-form-item>
        <a-form-item label="账号标识" required>
          <a-input v-model="accountForm.account_id" placeholder="账号唯一标识（如手机号、用户名），用于浏览器配置目录隔离" />
        </a-form-item>
        <a-form-item v-if="accountPlatform === 'yuanbao'" label="使用模型">
          <a-select v-model="accountForm.model" style="width: 100%;">
            <a-option value="DeepSeek">DeepSeek</a-option>
            <a-option value="Hunyuan">Hunyuan</a-option>
          </a-select>
        </a-form-item>
        <!-- 密码字段：编辑时默认隐藏，显示已设置状态 -->
        <a-form-item label="登录密码">
          <div v-if="editingAccount && !accountForm.change_password" style="display: flex; align-items: center; gap: 12px;">
            <span style="color: #52c41a;">● 已保存密码（不会显示明文）</span>
            <a-button type="text" size="small" @click="accountForm.change_password = true">修改密码</a-button>
          </div>
          <a-input-password
            v-else
            v-model="accountForm.password"
            :placeholder="editingAccount ? '请输入新密码，留空则不修改密码' : '可选，用于自动登录（也可后续在浏览器中手动登录）'"
          />
        </a-form-item>
        <a-form-item label="备注">
          <a-input v-model="accountForm.remark" placeholder="可选备注信息" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { aiConfigApi } from '@/api'

const activeTab = ref('types')

// 文章类型
const articleTypes = ref([])
const typeModalVisible = ref(false)
const editingType = ref(null)
const typeForm = ref({ name: '', prompt: '' })

// 提示词
const prompts = ref({ default_article_prompt: '', image_prompt: '' })
const savingPrompts = ref(false)

// 账号
const accountPlatform = ref('zhipu')
const accounts = ref([])
const accountModalVisible = ref(false)
const editingAccount = ref(null)
const accountForm = ref({ name: '', account_id: '', model: 'DeepSeek', remark: '', password: '', change_password: false })

// 分页相关（文章类型表格）
const articleTypeCurrentPage = ref(1)
const articleTypePageSize = ref(15)
const pagedArticleTypes = computed(() => {
  const start = (articleTypeCurrentPage.value - 1) * articleTypePageSize.value
  const end = start + articleTypePageSize.value
  return articleTypes.value.slice(start, end)
})
const articleTypePagination = computed(() => ({
  current: articleTypeCurrentPage.value,
  pageSize: articleTypePageSize.value,
  total: articleTypes.value.length,
  showTotal: true,
  showPageSize: true,
  pageSizeOptions: [10, 15, 20]
}))
const handleArticleTypePageChange = (page) => { articleTypeCurrentPage.value = page }
const handleArticleTypePageSizeChange = (size) => { articleTypePageSize.value = size; articleTypeCurrentPage.value = 1 }

// 分页相关（账号表格）
const accountCurrentPage = ref(1)
const accountPageSize = ref(15)
const pagedAccounts = computed(() => {
  const start = (accountCurrentPage.value - 1) * accountPageSize.value
  const end = start + accountPageSize.value
  return accounts.value.slice(start, end)
})
const accountPagination = computed(() => ({
  current: accountCurrentPage.value,
  pageSize: accountPageSize.value,
  total: accounts.value.length,
  showTotal: true,
  showPageSize: true,
  pageSizeOptions: [10, 15, 20]
}))
const handleAccountPageChange = (page) => { accountCurrentPage.value = page }
const handleAccountPageSizeChange = (size) => { accountPageSize.value = size; accountCurrentPage.value = 1 }

const platformNames = {
  zhipu: '智谱AI',
  yuanbao: '腾讯元宝',
  doubao: '豆包'
}

// 设置
const settings = ref({
  default_image_count: 3,
  default_ai_platform: 'zhipu',
  default_article_type: 'free'
})
const savingSettings = ref(false)

// 批量生成默认配置
const batchConfig = ref({
  article_platform: 'zhipu',
  article_account_id: '',
  image_platform: 'doubao',
  generate_images: true,
  image_count_per_chapter: 3
})

// 文章生成平台的账号列表
const articlePlatformAccounts = ref([])

// 加载文章平台账号
async function loadArticlePlatformAccounts() {
  try {
    const res = await aiConfigApi.getAccounts(batchConfig.value.article_platform)
    articlePlatformAccounts.value = res.list || []
  } catch (e) {
    console.error('加载文章平台账号失败', e)
  }
}

// 加载文章类型
async function loadArticleTypes() {
  try {
    const res = await aiConfigApi.getArticleTypes()
    articleTypes.value = res.list || []
  } catch (e) {
    console.error('加载文章类型失败', e)
  }
}

// 显示类型弹窗
function showTypeModal(record = null) {
  editingType.value = record
  if (record) {
    typeForm.value = { name: record.name, prompt: record.prompt || '' }
  } else {
    typeForm.value = { name: '', prompt: '' }
  }
  typeModalVisible.value = true
}

// 保存类型
async function saveType() {
  if (!typeForm.value.name) {
    Message.warning('请输入类型名称')
    return
  }
  try {
    if (editingType.value) {
      await aiConfigApi.updateArticleType(editingType.value.id, typeForm.value)
      Message.success('更新成功')
    } else {
      await aiConfigApi.createArticleType(typeForm.value)
      Message.success('新增成功')
    }
    typeModalVisible.value = false
    loadArticleTypes()
  } catch (e) {
    Message.error('保存失败')
  }
}

// 删除类型
async function deleteType(record) {
  try {
    await aiConfigApi.deleteArticleType(record.id)
    Message.success('删除成功')
    loadArticleTypes()
  } catch (e) {
    Message.error('删除失败')
  }
}

// 加载提示词
async function loadPrompts() {
  try {
    const res = await aiConfigApi.getPrompts()
    prompts.value = res
  } catch (e) {
    console.error('加载提示词失败', e)
  }
}

// 保存提示词
async function savePrompts() {
  savingPrompts.value = true
  try {
    await aiConfigApi.updatePrompts(prompts.value)
    Message.success('提示词保存成功')
  } catch (e) {
    Message.error('保存失败')
  } finally {
    savingPrompts.value = false
  }
}

// 加载账号
async function loadAccounts() {
  try {
    const res = await aiConfigApi.getAccounts(accountPlatform.value)
    accounts.value = res.list || []
  } catch (e) {
    console.error('加载账号失败', e)
  }
}

// 显示账号弹窗
function showAccountModal(record = null) {
  editingAccount.value = record
  if (record) {
    accountForm.value = {
      name: record.name,
      account_id: record.account_id,
      model: record.model || 'DeepSeek',
      remark: record.remark || '',
      password: '',
      change_password: false  // 编辑时默认不修改密码
    }
  } else {
    accountForm.value = { name: '', account_id: '', model: 'DeepSeek', remark: '', password: '', change_password: true }
  }
  accountModalVisible.value = true
}

// 保存账号
async function saveAccount() {
  if (!accountForm.value.name || !accountForm.value.account_id) {
    Message.warning('请填写账号名称和标识')
    return
  }
  try {
    // 构造提交数据
    const submitData = {
      name: accountForm.value.name,
      account_id: accountForm.value.account_id,
      model: accountForm.value.model,
      remark: accountForm.value.remark
    }
    // 只有修改密码时才发送密码字段
    if (accountForm.value.change_password && accountForm.value.password) {
      submitData.password = accountForm.value.password
    }
    // 新增账号时如果填了密码也发送
    if (!editingAccount.value && accountForm.value.password) {
      submitData.password = accountForm.value.password
    }

    if (editingAccount.value) {
      await aiConfigApi.updateAccount(accountPlatform.value, editingAccount.value.id, submitData)
      Message.success('更新成功')
    } else {
      await aiConfigApi.createAccount(accountPlatform.value, submitData)
      Message.success('新增成功')
    }
    accountModalVisible.value = false
    loadAccounts()
  } catch (e) {
    Message.error('保存失败')
  }
}

// 删除账号
async function deleteAccount(record) {
  try {
    await aiConfigApi.deleteAccount(accountPlatform.value, record.id)
    Message.success('删除成功')
    loadAccounts()
  } catch (e) {
    Message.error('删除失败')
  }
}

// 加载设置
async function loadSettings() {
  try {
    const res = await aiConfigApi.getSettings()
    settings.value = { ...settings.value, ...res }
    // 加载批量生成默认配置
    if (res.batch_generate) {
      batchConfig.value = { ...batchConfig.value, ...res.batch_generate }
    }
  } catch (e) {
    console.error('加载设置失败', e)
  }
}

// 保存设置
async function saveSettings() {
  savingSettings.value = true
  try {
    // 保存基础设置和批量生成配置
    const saveData = { ...settings.value, batch_generate: batchConfig.value }
    await aiConfigApi.updateSettings(saveData)
    Message.success('设置保存成功')
  } catch (e) {
    Message.error('保存失败')
  } finally {
    savingSettings.value = false
  }
}

// 监听文章生成平台变化，重新加载账号
watch(() => batchConfig.value.article_platform, () => {
  batchConfig.value.article_account_id = ''
  loadArticlePlatformAccounts()
})

onMounted(() => {
  loadArticleTypes()
  loadPrompts()
  loadAccounts()
  loadSettings()
  loadArticlePlatformAccounts()
  loadSettings()
})
</script>

<style scoped>
.ai-config-page {
  padding: 16px;
}
.config-section {
  padding: 8px 0;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 500;
}
.prompt-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  color: #666;
  font-size: 12px;
}
</style>
