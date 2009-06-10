package org.jmodelica.ide.editor;

import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.Iterator;

import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IProject;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.jface.action.Action;
import org.eclipse.jface.action.IMenuManager;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.preference.IPreferenceStore;
import org.eclipse.jface.preference.PreferenceConverter;
import org.eclipse.jface.text.IAutoEditStrategy;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IDocumentPartitioner;
import org.eclipse.jface.text.IRegion;
import org.eclipse.jface.text.ITextOperationTarget;
import org.eclipse.jface.text.ITextSelection;
import org.eclipse.jface.text.Position;
import org.eclipse.jface.text.presentation.IPresentationReconciler;
import org.eclipse.jface.text.presentation.PresentationReconciler;
import org.eclipse.jface.text.reconciler.DirtyRegion;
import org.eclipse.jface.text.reconciler.IReconciler;
import org.eclipse.jface.text.reconciler.IReconcilingStrategy;
import org.eclipse.jface.text.reconciler.MonoReconciler;
import org.eclipse.jface.text.rules.DefaultDamagerRepairer;
import org.eclipse.jface.text.rules.FastPartitioner;
import org.eclipse.jface.text.rules.ITokenScanner;
import org.eclipse.jface.text.source.Annotation;
import org.eclipse.jface.text.source.ISourceViewer;
import org.eclipse.jface.text.source.IVerticalRuler;
import org.eclipse.jface.text.source.SourceViewerConfiguration;
import org.eclipse.jface.text.source.projection.ProjectionAnnotation;
import org.eclipse.jface.text.source.projection.ProjectionAnnotationModel;
import org.eclipse.jface.util.PropertyChangeEvent;
import org.eclipse.swt.graphics.Color;
import org.eclipse.swt.graphics.RGB;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.IEditorInput;
import org.eclipse.ui.IFileEditorInput;
import org.eclipse.ui.IURIEditorInput;
import org.eclipse.ui.texteditor.AbstractDecoratedTextEditor;
import org.eclipse.ui.texteditor.AbstractDecoratedTextEditorPreferenceConstants;
import org.eclipse.ui.texteditor.SourceViewerDecorationSupport;
import org.eclipse.ui.views.contentoutline.IContentOutlinePage;
import org.jastadd.plugin.ReconcilingStrategy;
import org.jastadd.plugin.compiler.ast.IFoldingNode;
import org.jastadd.plugin.registry.ASTRegistry;
import org.jastadd.plugin.registry.IASTRegistryListener;
import org.jmodelica.ast.ASTNode;
import org.jmodelica.ast.BaseClassDecl;
import org.jmodelica.ast.InstProgramRoot;
import org.jmodelica.ast.SourceRoot;
import org.jmodelica.ast.StoredDefinition;
import org.jmodelica.ide.Constants;
import org.jmodelica.ide.ModelicaCompiler;
import org.jmodelica.ide.error.InstanceErrorHandler;
import org.jmodelica.ide.folding.AnnotationPosition;
import org.jmodelica.ide.folding.AnnotationProjectionAnnotation;
import org.jmodelica.ide.folding.ModelicaProjectionSupport;
import org.jmodelica.ide.folding.ModelicaProjectionViewer;
import org.jmodelica.ide.outline.InstanceOutlinePage;
import org.jmodelica.ide.outline.OutlinePage;
import org.jmodelica.ide.outline.SourceOutlinePage;
import org.jmodelica.ide.scanners.ModelicaCommentScanner;
import org.jmodelica.ide.scanners.ModelicaQIdentScanner;
import org.jmodelica.ide.scanners.ModelicaStringScanner;
import org.jmodelica.ide.scanners.generated.Modelica22AnnotationScanner;
import org.jmodelica.ide.scanners.generated.Modelica22DefenitionScanner;
import org.jmodelica.ide.scanners.generated.Modelica22NormalScanner;
import org.jmodelica.ide.scanners.generated.Modelica22PartitionScanner;

/**
 * Basic source editor with projection annotations and outline
 * 
 * @author emma
 * 
 */
public class Editor extends AbstractDecoratedTextEditor implements IASTRegistryListener {

	private static final RGB BRACE_MATCHING_COLOR = Constants.BRACE_MATCHING_COLOR;
	private static final String CURRENT_LINE_COLOR_KEY = AbstractDecoratedTextEditorPreferenceConstants.EDITOR_CURRENT_LINE_COLOR;
	private static final String CURRENT_LINE_KEY = AbstractDecoratedTextEditorPreferenceConstants.EDITOR_CURRENT_LINE;
	private static final String BRACE_MATCHING_KEY = Constants.KEY_BRACE_MATCHING;
	private static final String BRACE_MATCHING_COLOR_KEY = Constants.KEY_BRACE_MATCHING_COLOR;
	public static final String CONTENT_TYPE_ID = Constants.CONTENT_TYPE_ID;
	public static final String FILE_EXTENSION = Constants.FILE_EXTENSION;

	// Content outlines
	private OutlinePage fSourceOutlinePage;
	private InstanceOutlinePage fInstanceOutlinePage;

	// Reconciling strategy
	private ReconcilingStrategy fStrategy;

	// ASTRegistry listener fields
	private ASTRegistry fRegistry;
	private ASTNode fRoot;
	private String fKey;
	private IProject fProject;
	private IDocumentPartitioner fPartitioner;
	private ModelicaProjectionSupport projectionSupport;
	
	// Actions that needs to be altered
	private ErrorCheckAction errorCheckAction;
	private ToggleAnnotationsAction toggleAnnotationsAction;

	public Editor() {
		fRegistry = org.jastadd.plugin.Activator.getASTRegistry();
		fSourceOutlinePage = new SourceOutlinePage(this); 
		fInstanceOutlinePage = new InstanceOutlinePage(this);
		fStrategy = new ReconcilingStrategy();
	}

	/*
	 * Override to get projection annotations in the viewer
	 * (non-Javadoc)
	 * @see org.eclipse.ui.texteditor.AbstractDecoratedTextEditor#createSourceViewer(org.eclipse.swt.widgets.Composite, org.eclipse.jface.text.source.IVerticalRuler, int)
	 */
	@Override
	protected ISourceViewer createSourceViewer(Composite parent,
			IVerticalRuler ruler, int styles) {
		
		// Code from the super class implementation of this method
		fAnnotationAccess = getAnnotationAccess();
		fOverviewRuler = createOverviewRuler(getSharedColors());
		
		// Projection support
		ModelicaProjectionViewer viewer = new ModelicaProjectionViewer(parent, ruler, getOverviewRuler(), isOverviewRulerVisible(), styles);
	    configureProjectionSupport(viewer);
	    configureDecorationSupport(viewer);
		
		return viewer;
	}

	private void configureProjectionSupport(ModelicaProjectionViewer viewer) {
		projectionSupport = new ModelicaProjectionSupport(viewer, getAnnotationAccess(), getSharedColors());
	    projectionSupport.addSummarizableAnnotationType(ModelicaCompiler.ERROR_MARKER_ID);
	    projectionSupport.setCursorLineBackground(getCursorLineBackground());
	    projectionSupport.install();
	}

	private void configureDecorationSupport(ModelicaProjectionViewer viewer) {
		// Set default values for brace matching.
	    IPreferenceStore preferenceStore = getPreferenceStore();
		preferenceStore.setDefault(BRACE_MATCHING_KEY, true);
	    PreferenceConverter.setDefault(preferenceStore, BRACE_MATCHING_COLOR_KEY, BRACE_MATCHING_COLOR);
	    // Configure brace matching and ensure decoration support has been created and configured.
		SourceViewerDecorationSupport decoration = getSourceViewerDecorationSupport(viewer);
		decoration.setCharacterPairMatcher(new ModelicaCharacterPairMatcher(viewer));
		decoration.setMatchingCharacterPainterPreferenceKeys(BRACE_MATCHING_KEY, BRACE_MATCHING_COLOR_KEY);
	}

	
	@Override
	protected void handlePreferenceStoreChanged(PropertyChangeEvent event) {
		String property = event.getProperty();
		if (property.equals(CURRENT_LINE_KEY) || property.equals(CURRENT_LINE_COLOR_KEY))
		    projectionSupport.setCursorLineBackground(getCursorLineBackground());
		super.handlePreferenceStoreChanged(event);
	}

	private Color getCursorLineBackground() {
		IPreferenceStore preferenceStore = getPreferenceStore();
		if (!preferenceStore.getBoolean(CURRENT_LINE_KEY))
			return null;
		RGB color = PreferenceConverter.getColor(preferenceStore, CURRENT_LINE_COLOR_KEY);
		return new Color(Display.getCurrent(), color);
	}

	/*
	 * Override to set the configuration of the source viewer and to update on creation
	 * (non-Javadoc)
	 * @see org.eclipse.ui.texteditor.AbstractDecoratedTextEditor#createPartControl(org.eclipse.swt.widgets.Composite)
	 */
	@Override
	public void createPartControl(Composite parent) {

		 // Set the source viewer configuration before the call to createPartControl to set viewer configuration
	    super.setSourceViewerConfiguration(new ViewerConfiguration());
	    super.createPartControl(parent);
	    
	    update();
	}
	
	/*
	 * Override to create an outline page
	 * (non-Javadoc)
	 * @see org.eclipse.ui.texteditor.AbstractDecoratedTextEditor#getAdapter(java.lang.Class)
	 */
	@SuppressWarnings("unchecked")
	@Override
	public Object getAdapter(Class required) {
		if (IContentOutlinePage.class.equals(required)) {
			return fSourceOutlinePage;
		}
		return super.getAdapter(required);
	}

	public IContentOutlinePage getSourceOutlinePage() {
		return fSourceOutlinePage;
	}

	public IContentOutlinePage getInstanceOutlinePage() {
		return fInstanceOutlinePage;
	}

	/**
	 * Override this method to reset the AST when the input changes 
	 * the editor input change. 
	 */
	@Override
	protected void doSetInput(IEditorInput input) throws CoreException {
		super.doSetInput(input);

		IFileEditorInput fInput = null;
		if (input instanceof IFileEditorInput) 
			fInput = (IFileEditorInput)input;
		resetAST(fInput);
		fStrategy.setFile(fInput == null ? null : fInput.getFile());
		if (fRoot == null) 
			compileExternal(input);
	}

	@Override
	protected void createActions() {
		super.createActions();
		
		setAction(Constants.ACTION_EXPAND_ALL_ID, new ExpandAllAction());
		setAction(Constants.ACTION_COLLAPSE_ALL_ID, new CollapseAllAction());
		setAction(Constants.ACTION_ERROR_CHECK_ID, errorCheckAction = new ErrorCheckAction());
		setAction(Constants.ACTION_TOGGLE_ANNOTATIONS_ID, toggleAnnotationsAction = new ToggleAnnotationsAction());
		updateErrorCheckAction();
	}
	
	@Override
	protected void rulerContextMenuAboutToShow(IMenuManager menu) {
		super.rulerContextMenuAboutToShow(menu);
		addAction(menu, Constants.ACTION_EXPAND_ALL_ID);
		addAction(menu, Constants.ACTION_COLLAPSE_ALL_ID);
	}

	private void compileExternal(IEditorInput input) {
		try {
			IFile file = null;
			if (input instanceof IFileEditorInput) 
				file = ((IFileEditorInput) input).getFile();
			String path = getPathOfInput(input);
			if (path != null) {
				ModelicaCompiler cmp = new ModelicaCompiler();
				fRoot = cmp.compileFile(file, path);
			}
		} catch (IllegalArgumentException e) {
		}
		update();
	}

	private String getPathOfInput(IEditorInput input) {
		String path = null;
		try {
			if (input instanceof IFileEditorInput) {
				IFile file = ((IFileEditorInput) input).getFile();
				path = file.getRawLocation().toOSString();
			} else if (input instanceof IURIEditorInput) {
				URI uri = ((IURIEditorInput) input).getURI();
				path = new File(uri).getCanonicalPath();
			}
		} catch (IOException e) {
		}
		return path;
	}

	// ASTRegistry listener methods
	
	public void childASTChanged(IProject project, String key) {
		if (project == fProject && key.equals(fKey)) {
			fRoot = (ASTNode) fRegistry.lookupAST(fKey, fProject);
			update();
		}
	}

	public void projectASTChanged(IProject project) {
		if (project == fProject) {
			fRoot = (ASTNode) fRegistry.lookupAST(fKey, fProject);
			update();
		}
	}

	/**
	 * Update to the AST corresponding to the file input
	 * @param fInput The new file input
	 */
	private void resetAST(IFileEditorInput fInput) {
		// Reset 
		fRegistry.removeListener(this);
		fRoot = null;
		fProject = null;
		fKey = null;
		
		// Update
		if (fInput != null) {
			IFile file = fInput.getFile();
			fKey = file.getRawLocation().toOSString();
			fProject = file.getProject();			
			fRoot = (ASTNode) fRegistry.lookupAST(fKey, fProject);
			fRegistry.addListener(this, fProject, fKey);
			update();
		}
	}
	
	
	/**
	 * Updates the outline and the view
	 */
	private void update() {
		if (getSourceViewer() != null && fRoot != null) {
			IDocument document = getSourceViewer().getDocument();
			if (document != null) 
				setupDocumentPartitioner(document);
			((StoredDefinition) fRoot).setDocument(document);
			// Update outline
			fSourceOutlinePage.updateAST(fRoot);
			fInstanceOutlinePage.updateAST(fRoot);
			// Update folding
			updateProjectionAnnotations();
			updateErrorCheckAction();
		}
	}
	
	private void setupDocumentPartitioner(IDocument document) {
		IDocumentPartitioner wanted = getDocumentPartitioner();
		IDocumentPartitioner current = document.getDocumentPartitioner();
		if (wanted != current) {
			if (current != null)
				current.disconnect();
			wanted.connect(document);
			document.setDocumentPartitioner(wanted);
		}
	}

	private IDocumentPartitioner getDocumentPartitioner() {
		if (fPartitioner == null) {
			Modelica22PartitionScanner scanner = new Modelica22PartitionScanner();
			fPartitioner = new FastPartitioner(scanner, Modelica22PartitionScanner.LEGAL_PARTITIONS);
		}
		return fPartitioner;
	}

	/**
	 * Update projection annotations
	 */
	private void updateProjectionAnnotations() {
		
		ModelicaProjectionViewer viewer = (ModelicaProjectionViewer)getSourceViewer();
		if (viewer == null) 
			return;
		
		// Enable projection
		viewer.enableProjection();

		ProjectionAnnotationModel model = viewer.getProjectionAnnotationModel(); 
		if (model == null) 
			return;

		// Collect old annotations
		Collection<Annotation> oldAnnotationsC = new ArrayList<Annotation>();
		for (Iterator<Annotation> itr = model.getAnnotationIterator(); itr.hasNext();) 
			oldAnnotationsC.add(itr.next());
		Annotation[] oldAnnotations = oldAnnotationsC.toArray(new Annotation[] {});

		// Collect new annotations
		HashMap<Annotation,Position> newAnnotations = new HashMap<Annotation,Position>();
		if (fRoot instanceof IFoldingNode) {
			IFoldingNode node = (IFoldingNode) fRoot;
			IDocument document = getSourceViewer().getDocument();
			Collection<Position> positions = node.foldingPositions(document);
			for (Position pos : positions) {
				ProjectionAnnotation annotation;
				if (pos instanceof AnnotationPosition) {
					annotation = new AnnotationProjectionAnnotation();
					if (!toggleAnnotationsAction.isVisible())
						annotation.markCollapsed();
				} else {
					annotation = new ProjectionAnnotation();
				}
				newAnnotations.put(annotation, pos);
			}
		}

		// TODO: Only replace annotations that have changed, so that the state of the others are kept
		// Update annotations
		model.modifyAnnotations(oldAnnotations, newAnnotations, null);
	}

	@Override
	protected void handleCursorPositionChanged() {
		super.handleCursorPositionChanged();
		updateErrorCheckAction();
	}
	
	private void updateErrorCheckAction() {
		try {
			ITextSelection sel = (ITextSelection) getSelectionProvider().getSelection();
			errorCheckAction.setCurClass(fRoot.containingClass(sel.getOffset(), sel.getLength()));
		} catch (NullPointerException e) {
		}
	}

	public boolean selectNode(ASTNode node) {
		String path = getPathOfInput(getEditorInput());
		if (!path.equals(node.containingFileName()))
			return false;
		
		IDocument doc = getSourceViewer().getDocument();
		ASTNode sel = node.getSelectionNode();
		int offset = sel.getOffset(doc);
		int length = sel.getLength(doc);
		if (offset >= 0 && length >= 0) 
			selectAndReveal(offset, length);

		return true;
	}

	/**
	 * Source viewer configuration which provides the projection viewer with a
	 * presentation reconciler ...
	 * 
	 * @author emma
	 * 
	 */
	private class ViewerConfiguration extends SourceViewerConfiguration {

		private IndentationStrategy indentationStrategy;

		@Override
		public IAutoEditStrategy[] getAutoEditStrategies(
				ISourceViewer sourceViewer, String contentType) {
			return new IAutoEditStrategy[] { getIndentationStrategy() };
		}

		private IndentationStrategy getIndentationStrategy() {
			if (indentationStrategy == null)
				indentationStrategy = new IndentationStrategy();
			return indentationStrategy;
		}

		@Override
		public String[] getDefaultPrefixes(ISourceViewer sourceViewer,
				String contentType) {
			return new String[] { "//" };
		}

		@Override
		public String[] getConfiguredContentTypes(ISourceViewer sourceViewer) {
			return Constants.CONFIGURED_CONTENT_TYPES;
		}

		// Override methods in the super class to get a specialized hover,
		// content assist etc
		@Override
		public IPresentationReconciler getPresentationReconciler(ISourceViewer sourceViewer) {
			// The scanner is set via the PresentationReconciler and a
			// DamageRepairer
			PresentationReconciler reconciler = new PresentationReconciler();
			addScanner(reconciler, new Modelica22NormalScanner(), false,
					Modelica22PartitionScanner.NORMAL_PARTITION);
			addScanner(reconciler, new Modelica22DefenitionScanner(), false,
					Modelica22PartitionScanner.DEFINITION_PARTITION);
			addScanner(reconciler, new ModelicaStringScanner(), false,
					Modelica22PartitionScanner.STRING_PARTITION);
			addScanner(reconciler, new ModelicaQIdentScanner(), false,
					Modelica22PartitionScanner.QIDENT_PARTITION);
			addScanner(reconciler, new ModelicaCommentScanner(), false,
					Modelica22PartitionScanner.COMMENT_PARTITION);
			addScanner(reconciler, new Modelica22AnnotationScanner(), true,
					Modelica22PartitionScanner.ANNOTATION_PARTITION);
			return reconciler;
		}

		private void addScanner(PresentationReconciler reconciler,
				ITokenScanner scanner, boolean restart, String type) {
			DefaultDamagerRepairer dr;
			if (restart)
				dr = new RestartDamagerRepairer(scanner);
			else
				dr = new DefaultDamagerRepairer(scanner);
			reconciler.setDamager(dr, type);
			reconciler.setRepairer(dr, type);
		}
		
		@Override 
		public IReconciler getReconciler(ISourceViewer sourceViewer) {
			return new MonoReconciler(fStrategy, false);
	    }
	}

	private class DoOperationAction extends Action {
		private int action;

		public DoOperationAction(String text, int action) {
			super(text);
			this.action = action;
		}
		
		@Override
		public void run() {
			ISourceViewer sourceViewer = getSourceViewer();
			if (sourceViewer instanceof ITextOperationTarget) {
				((ITextOperationTarget) sourceViewer).doOperation(action);
			}
		}
	}

	private class ExpandAllAction extends DoOperationAction {
		public ExpandAllAction() {
			super("&Expand All", ModelicaProjectionViewer.EXPAND_ALL);
		}
	}

	private class CollapseAllAction extends DoOperationAction {
		public CollapseAllAction() {
			super("&Collapse All", ModelicaProjectionViewer.COLLAPSE_ALL);
		}
	}
	
	private class ConnectedTextsAction extends Action {
		protected void setTexts(String text) {
			setText(text);
			setToolTipText(text);
			setDescription(text);
		}
	}
	
	private class ToggleAnnotationsAction extends ConnectedTextsAction {
		private boolean visible;

		public ToggleAnnotationsAction() {
			super();
			update(false);
		}

		public boolean isVisible() {
			return visible;
		}

		@Override
		public void run() {
			update(!visible);
			int action = visible ? ModelicaProjectionViewer.EXPAND_ANNOTATIONS : ModelicaProjectionViewer.COLLAPSE_ANNOTATIONS;
			ISourceViewer sourceViewer = getSourceViewer();
			if (sourceViewer instanceof ITextOperationTarget) {
				((ITextOperationTarget) sourceViewer).doOperation(action);
			}
		}

		private void update(boolean visible) {
			this.visible = visible;
			setChecked(visible);
		}
	}

	private class ErrorCheckAction extends ConnectedTextsAction {
		private BaseClassDecl currentClass;

		public ErrorCheckAction() {
			setTexts(Constants.ACTION_ERROR_CHECK_TEXT);
			setEnabled(false);
		}

		public void setCurClass(BaseClassDecl currentClass) {
			if (currentClass != this.currentClass) {
				this.currentClass = currentClass;
				if (currentClass != null) {
					setTexts("Check " + currentClass.getName().getID() + " for errors");
					setEnabled(true);
				} else {
					setTexts(Constants.ACTION_ERROR_CHECK_TEXT);
					setEnabled(false);
				}
			}
		}

		@Override
		public void run() {
			performSave(true, null);
			SourceRoot root = (SourceRoot) currentClass.root();
			InstProgramRoot ipr = root.getProgram().getInstProgramRoot();
			InstanceErrorHandler errorHandler = (InstanceErrorHandler) root.getErrorHandler();
			errorHandler.resetCounter();
			ipr.retrieveInstFullClassDecl(currentClass.qualifiedName()).collectErrors();
			int num = errorHandler.getNumErrors();
			String msg;
			if (num == 0) 
				msg = "No errors found.";
			else
				msg = num + " errors found.";
			String title = "Checking " + currentClass.getName().getID() + " for errors:";
			MessageDialog.openInformation(new Shell(), title, msg);
		}
	}
}
